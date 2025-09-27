from httpx import AsyncClient


class TestPromptEndpoints:
    """Test basic functionality of prompt endpoints."""

    async def test_read_prompt(self, client: AsyncClient, auth_headers: dict):
        """Test reading the current prompt configuration."""
        response = await client.get("/api/prompt/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "role" in data
        assert "crypto_role" in data
        assert "suggest_post" in data
        assert "post_examples" in data
        assert isinstance(data["post_examples"], list)

    async def test_edit_prompt(self, client: AsyncClient, auth_headers: dict):
        """Test updating the prompt configuration."""
        # First, read the current prompt
        response = await client.get("/api/prompt/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Modify some fields
        updated_data = {
            "id": data["id"],
            "role": data["role"] + " Updated",
            "crypto_role": data["crypto_role"] + " Updated",
            "suggest_post": data["suggest_post"] + " Updated",
            "post_examples": data["post_examples"],
        }

        # Send update request
        update_response = await client.put(
            "/api/prompt/",
            headers=auth_headers,
            json=updated_data
        )
        assert update_response.status_code == 200
        updated_response_data = update_response.json()
        assert updated_response_data["role"] == updated_data["role"]

    async def test_add_post_example(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test adding a new post example."""
        test_example = "This is a test post example"
        await client.get("/api/prompt/", headers=auth_headers)
        response = await client.post(
            "/api/prompt/examples",
            headers=auth_headers,
            json={"example": test_example}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "post_examples" in data
        assert test_example in data["post_examples"]

    async def test_delete_post_example(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test removing a post example."""
        # First add an example to delete
        await client.get("/api/prompt/", headers=auth_headers)
        test_example = "Example to delete"
        add_response = await client.post(
            "/api/prompt/examples",
            headers=auth_headers,
            json={"example": test_example}
        )
        assert add_response.status_code in [200, 201]

        # Then delete it
        delete_response = await client.post(
            "/api/prompt/examples/delete",
            headers=auth_headers,
            json={"example": test_example}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert "post_examples" in data
        assert test_example not in data["post_examples"]

    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that endpoints require authentication."""
        # Test read without auth
        response = await client.get("/api/prompt/")
        assert response.status_code == 401

        # Test add without auth
        response = await client.post(
            "/api/prompt/examples",
            json={"example": "test"}
        )
        assert response.status_code == 401

        # Test delete without auth
        response = await client.post(
            "/api/prompt/examples/delete",
            json={"example": "test"}
        )
        assert response.status_code == 401

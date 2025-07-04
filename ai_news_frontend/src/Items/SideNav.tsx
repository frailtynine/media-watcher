import { Button, VStack } from "@chakra-ui/react";
import LogoutButton from "./LogoutButton";
import { authApi } from "../api";
import { useComponent } from "../hooks/Сomponent";
import AllTasks from "../Pages/Dashboard";
import Settings from "../Pages/Settings";
import LiveResults from "./LiveResults";

export default function SideNav() {
  const { setCurrentComponent } = useComponent();

  const handleLogout = () => {
    authApi.logout();
    setCurrentComponent(null);
  };
  return (
    <VStack p={4}>
      <Button
        colorScheme="teal"
        variant="solid"
        w={"100%"}
        onClick={() => setCurrentComponent(<AllTasks />)}
      >
        Tasks
      </Button>
      <Button
        colorScheme="teal"
        variant="solid"
        w={"100%"}
        onClick={() => setCurrentComponent(<LiveResults />)}
      >
        Live Results
      </Button>
      <Button
        colorScheme="teal"
        variant="solid"
        w={"100%"}
        onClick={() => setCurrentComponent(<Settings />)}
      >
        Settings
      </Button>
      <LogoutButton handleLogout={handleLogout}/>
    </VStack>
  );
}
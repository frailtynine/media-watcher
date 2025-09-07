import { useEffect, useState } from "react";
import Login from "../Items/Login";
import { useComponent } from "../hooks/Сomponent";
import { authApi } from "../api";
import { Box, Flex } from "@chakra-ui/react";
import AllTasks from "./Dashboard";
import SideNav from "../Items/SideNav";

export default function Main() {
  const { currentComponent, setCurrentComponent } = useComponent();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
    const checkInitialAuth = async () => {
      try {
        const token = authApi.getToken();
        if (!token) {
          setIsAuthenticated(false);
          setCurrentComponent(<Login />);
          setIsLoading(false);
          return;
        }

        const auth = await authApi.isAuthenticated();
        setIsAuthenticated(auth);
        
        if (auth) {
          setCurrentComponent(<AllTasks />);
        } else {
          authApi.removeToken(); // Clean up invalid token
          setCurrentComponent(<Login />);
        }
      } catch (error) {
        console.error("Error checking authentication:", error);
        setIsAuthenticated(false);
        authApi.removeToken();
        setCurrentComponent(<Login />);
      }
      setIsLoading(false);
    };
    
    checkInitialAuth();
  }, []); // Only run once on mount

  // Handle authentication state changes from login/logout
  useEffect(() => {
    const handleAuthSuccess = () => {
      setIsAuthenticated(true);
      setCurrentComponent(<AllTasks />);
    };

    const handleAuthLogout = () => {
      setIsAuthenticated(false);
      setCurrentComponent(<Login />);
    };

    window.addEventListener('auth-login', handleAuthSuccess);
    window.addEventListener('auth-logout', handleAuthLogout);

    return () => {
      window.removeEventListener('auth-login', handleAuthSuccess);
      window.removeEventListener('auth-logout', handleAuthLogout);
    };
  }, [setCurrentComponent]);

  

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      {isAuthenticated ? (
        <Flex h="100vh">
          <Box width="200px" bg="gray.100" position={"fixed"} height="100vh">
            <SideNav />
          </Box>
          <Box flexGrow={1} p={8} overflowY={"auto"} marginLeft={"200px"}>
              {currentComponent}
          </Box>
        </Flex>

      ) : (
        <Login />
      )}
    </>
  );
}
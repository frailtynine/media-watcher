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
    const checkAuth = async () => {
      if (authApi.isAuthenticated()) {
        try {
          setIsAuthenticated(true);
          if (!currentComponent) {
            setCurrentComponent(<AllTasks />);
          }
        } catch (error) {
          authApi.logout();
          setCurrentComponent(null);
        }
      } else {
        setCurrentComponent(null);
      }
      setIsLoading(false);
    };
    
    checkAuth();
  }, [currentComponent, setCurrentComponent]);

  

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
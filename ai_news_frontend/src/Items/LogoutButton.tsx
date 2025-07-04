import { Button } from "@chakra-ui/react";


export default function LogoutButton({ handleLogout }: { handleLogout: () => void }) {
  return (
    <Button 
      colorScheme="red" 
      onClick={handleLogout} 
      alignSelf="flex-end"
      w={"100%"}
      >
        Logout
    </Button>

  )
}


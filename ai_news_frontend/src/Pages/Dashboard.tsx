import { Box, Heading, Button, Flex } from "@chakra-ui/react";
import { newsTaskApi, cryptoTaskApi } from "../api";
import NewsTaskCard from "../Items/NewsTaskCard";
import CryptoTaskCard from "../Items/CryptoTaskCard";
import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { NewsTask, NewsTaskCreate, CryptoTask, CryptoTaskCreate } from "../interface";

export default function AllTasks() {
  const [newsTasks, setNewsTasks] = useState<NewsTask[]>([]);
  const [cryptoTasks, setCryptoTasks] = useState<CryptoTask[]>([]);
  const [createdTask, setCreatedTask] = useState<ReactNode>(null);
  
  useEffect(() => {
    const fetchNewsTasks = async () => {
      try {
        const tasks = await newsTaskApi.getTasks();
          setNewsTasks(tasks);
      } catch (error) {
        console.error("Failed to fetch news tasks:", error);
      }
    };

    const fetchCryptoTasks = async () => {
      try {
        const tasks = await cryptoTaskApi.getTasks();
        setCryptoTasks(tasks);
      } catch (error) {
        console.error("Failed to fetch crypto tasks", error);
      }
    }

    fetchNewsTasks();
    fetchCryptoTasks();
  }, []);
  
  // NewsTask handlers 
  const handleCreateNewsTask = async (task: NewsTaskCreate) => {
    try {
      await newsTaskApi.createTask(task);
      setCreatedTask(null);
    } catch (error) {
      console.error("Failed to create news task:", error);
    }
  };

  const handleDeleteNewsTask = async (taskId: number) => {
    try {
      await newsTaskApi.deleteTask(taskId);
      setNewsTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error("Failed to delete news task:", error);
    }
  };

  const handleEditNewsTask = async (task: NewsTask) => {
    try {
      const updatedTask = await newsTaskApi.updateTask(task.id, task);
      if (updatedTask) {
        setNewsTasks((prevTasks) =>
          prevTasks.map((t) => (t.id === updatedTask.id ? updatedTask : t))
        );
      }
    } catch (error) {
      console.error("Failed to update news task:", error);
    }
  };

  // CryptoTask handlers
  const handleCreateCryptoTask = async (task: CryptoTaskCreate) => {
    try {
      await cryptoTaskApi.createTask(task);
      setCreatedTask(null);
    } catch (error) {
      console.error("Failed to create crypto task:", error);
    }
  };

  const handleDeleteCryptoTask = async (taskId: number) => {
    try {
      await cryptoTaskApi.deleteTask(taskId);
      setCryptoTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error("Failed to delete crypto task:", error);
    }
  };

  const handleEditCryptoTask = async (task: CryptoTask) => {
    console.log("Editing task:", task);
    try {
      const updatedTask = await cryptoTaskApi.updateTask(task.id, task);
      console.log("Updated task:", updatedTask);
      if (updatedTask) {
        setCryptoTasks((prevTasks) =>
          prevTasks.map((t) => (t.id === updatedTask.id ? updatedTask : t))
        );
      }
    } catch (error) {
      console.error("Failed to update crypto task:", error);
    }
  };

  return (
   <Box>
     <Heading mb={4}>Dashboard</Heading>
     <Flex direction={"row"} justifyContent={"flex-end"}>
      <Button
        colorScheme="teal"
        variant="solid"
        m={4}
        onClick={() => {
          setCreatedTask(
            <NewsTaskCard
            onCreate={handleCreateNewsTask}
            />
          )
        }}
        >
        Create News Task
      </Button>
      <Button
        colorScheme="teal"
        variant="solid"
        m={4}
        onClick={() => {
          setCreatedTask(
            <CryptoTaskCard
            onCreate={handleCreateCryptoTask}
            />
          )
        }}
        >
        Create Crypto Task
      </Button>
    </Flex>
     {createdTask}
     <Flex gap={4} flexWrap={"wrap"}>
     {newsTasks.length > 0 ? (
       newsTasks.map((task) => (
        <Box maxWidth="calc(25% - 12px)" minWidth="250px" m={4}>
          <NewsTaskCard
           key={task.id}
           newsTask={task}
           onDelete={handleDeleteNewsTask}
           onEdit={handleEditNewsTask}
         />
        </Box>
       ))
     ) : null}
     {cryptoTasks.length > 0 ? (
        cryptoTasks.map((task) => (
          <Box maxWidth="calc(25% - 12px)" minWidth="250px">
            <CryptoTaskCard
               key={task.id}
              cryptoTask={task}
              onDelete={handleDeleteCryptoTask}
              onEdit={handleEditCryptoTask}
            />
          </Box>
        ))
     ): null}
     </Flex>
   </Box>
  );
}
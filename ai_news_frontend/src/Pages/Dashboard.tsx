import { Box, Heading, Button, Flex } from "@chakra-ui/react";
import { newsTaskApi } from "../api";
import NewsTaskCard from "../Items/NewsTaskCard";
import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { NewsTask, NewsTaskCreate } from "../interface";

export default function AllTasks() {
  const [newsTasks, setNewsTasks] = useState<NewsTask[]>([]);
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

    fetchNewsTasks();
  }, []);

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
    console.log("Editing task:", task);
    try {
      const updatedTask = await newsTaskApi.updateTask(task.id, task);
      console.log("Updated task:", updatedTask);
      if (updatedTask) {
        setNewsTasks((prevTasks) =>
          prevTasks.map((t) => (t.id === updatedTask.id ? updatedTask : t))
        );
      }
    } catch (error) {
      console.error("Failed to update news task:", error);
    }
  };

  return (
   <Box>
     <Heading mb={4}>Dashboard</Heading>
      <Button
        colorScheme="teal"
        variant="solid"
        mb={4}
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
     {createdTask}
     <Flex gap={4}>
     {newsTasks.length > 0 ? (
       newsTasks.map((task) => (
         <NewsTaskCard
          key={task.id}
          newsTask={task}
          onDelete={handleDeleteNewsTask}
          onEdit={handleEditNewsTask}
        />
       ))
     ) : null}
     </Flex>
   </Box>
  );
}
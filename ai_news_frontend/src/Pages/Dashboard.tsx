import { Box, Heading, Button, Flex, Table, } from "@chakra-ui/react";
import { newsTaskApi } from "../api";
import NewsTaskCard from "../Items/NewsTaskCard";
import { useState, useEffect } from "react";
import type { NewsTask, NewsTaskCreate, } from "../interface";
import { useComponent } from "../hooks/Сomponent";


export default function AllTasks() {
  const [newsTasks, setNewsTasks] = useState<NewsTask[]>([]);
  const { setCurrentComponent } = useComponent();
  
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
  

  // NewsTask handlers 
  const handleCreateNewsTask = async (task: NewsTaskCreate) => {
    try {
      await newsTaskApi.createTask(task);
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


  return (
   <Box>
     <Heading mb={4}>Dashboard</Heading>
     <Flex direction={"row"} justifyContent={"flex-end"}>
      <Button
        colorScheme="teal"
        variant="solid"
        m={4}
        onClick={() => {
          setCurrentComponent(
            <NewsTaskCard
              onCreate={handleCreateNewsTask}
              onEdit={handleEditNewsTask}
              onDelete={handleDeleteNewsTask}
            />
          )
        }}
        >
        Create News Task
      </Button>
    </Flex>
    <Table.Root striped size={"sm"}>
      <Table.Header>
        <Table.Row>
          <Table.Cell>Title</Table.Cell>
          <Table.Cell>End Date</Table.Cell>
          <Table.Cell>Actions</Table.Cell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {newsTasks.length > 0 ? (
          newsTasks.map((task) => (
            <NewsTaskCard
              key={task.id}
              newsTask={task}
              onDelete={handleDeleteNewsTask}
              onEdit={handleEditNewsTask}
              listView={true}
            />
          ))
        ) : (
          <Table.Row>
            <Table.Cell colSpan={3}>No news tasks available</Table.Cell>
          </Table.Row>
        )}
      </Table.Body>
    </Table.Root>
   </Box>
  );
}
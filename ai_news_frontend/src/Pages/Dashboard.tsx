import { Box, Heading, Button, Flex, Table, IconButton } from "@chakra-ui/react";
import { newsTaskApi, cryptoTaskApi, eventsAPI} from "../api";
import NewsTaskCard from "../Items/NewsTaskCard";
import CryptoTaskCard from "../Items/CryptoTaskCard";
import { useState, useEffect } from "react";
import type { NewsTask, NewsTaskCreate, CryptoTask, CryptoTaskCreate, Event } from "../interface";
import { useComponent } from "../hooks/Сomponent";
import EventItem from "../Items/Event";
import { HiRefresh } from "react-icons/hi";


export default function AllTasks() {
  const [newsTasks, setNewsTasks] = useState<NewsTask[]>([]);
  const [cryptoTasks, setCryptoTasks] = useState<CryptoTask[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
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

    const fetchCryptoTasks = async () => {
      try {
        const tasks = await cryptoTaskApi.getTasks();
        setCryptoTasks(tasks);
      } catch (error) {
        console.error("Failed to fetch crypto tasks", error);
      }
    }

    const fetchEvents = async () => {
      try {
        const response = await eventsAPI.getAll();
        setEvents(response);
      } catch (error) {
        console.error("Failed to fetch events:", error);
      }
    };

    fetchNewsTasks();
    fetchCryptoTasks();
    fetchEvents();
  }, []);
  
  // Event handlers
  const handlePauseEvent = async (eventId: string) => {
    try {
      const updatedEvent = await eventsAPI.customCall('GET', `${eventId}/toggle_pause`);
      setEvents((prevEvents) =>
        prevEvents.map((event) => (event.id === updatedEvent.id ? updatedEvent : event))
      );
    } catch (error) {
      console.error("Failed to pause event:", error);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    try {
      await eventsAPI.delete(eventId);
      setEvents((prevEvents) => prevEvents.filter((event) => event.id !== eventId));
    } catch (error) {
      console.error("Failed to delete event:", error);
    }
  };

  const handleEventsRefresh = async () => {
    try {
      const refreshedEvents = await eventsAPI.customCall('GET', 'refresh');
      setEvents(refreshedEvents);
    } catch (error) {
      console.error("Failed to refresh events:", error);
    }
  }

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

  // CryptoTask handlers
  const handleCreateCryptoTask = async (task: CryptoTaskCreate) => {
    try {
      await cryptoTaskApi.createTask(task);
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
      <IconButton
        aria-label="Refresh Events"
        onClick={handleEventsRefresh}
        colorScheme="blue"
        size="sm"
        m={2}
      >
        <HiRefresh />
      </IconButton>
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
      <Button
        colorScheme="teal"
        variant="solid"
        m={4}
        onClick={() => {
          setCurrentComponent(
            <CryptoTaskCard
            onCreate={handleCreateCryptoTask}
            />
          )
        }}
        >
        Create Crypto Task
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
        {events.length > 0 && (events.map((item) => (
          <EventItem
            key={item.id}
            event={item}
            onPause={handlePauseEvent}
            onDelete={handleDeleteEvent}
            listView
          />
        )))}
      </Table.Body>
    </Table.Root>
     <Flex gap={4} flexWrap={"wrap"}>
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
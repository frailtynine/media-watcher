import { Card, Text, Box, Flex, IconButton, Input, Stack, Table } from "@chakra-ui/react";
import { Textarea } from "@chakra-ui/react";
import type { NewsTask, NewsTaskCreate } from "../interface";
import { FiEdit2, FiCheck } from "react-icons/fi";
import { FaPause, FaPlay, FaBan, FaRegCheckCircle } from "react-icons/fa";
import { MdDelete } from "react-icons/md";
import { MdRefresh } from "react-icons/md";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { FaRegCopy } from "react-icons/fa";
import { useComponent } from "../hooks/Сomponent";
import AllTasks from "../Pages/Dashboard";
import { newsTaskApi } from "../api";


interface NewsTaskCardProps {
  newsTask?: NewsTask;
  onEdit?: (newsTask: NewsTask) => void;
  onCreate?: (newsTask: NewsTaskCreate) => void;
  onDelete?: (newsTaskId: number) => void;
  listView?: boolean;
  editMode?: boolean;
  onCheck?: (newsTask: NewsTask) => void;
}

export default function NewsTaskCard({ newsTask, onEdit, onCreate, onDelete, listView, editMode, onCheck }: NewsTaskCardProps) {
  const { setCurrentComponent } = useComponent();

  // useForm for create mode
  const {
    register,
    handleSubmit,
    reset,
  } = useForm<NewsTaskCreate>({
    defaultValues: {
      title: "",
      description: "",
      end_date: "",
      link: "",
      relevant_news: [],
      non_relevant_news: [],
    },
  });

  // Local state for edit mode
  const [task, setTask] = useState<NewsTask>(newsTask || ({} as NewsTask));
  const [newRelevantNews, setNewRelevantNews] = useState(""); // Add this for input
  const [newNonRelevantNews, setNewNonRelevantNews] = useState(""); // Add this for input
  const [checkedRelevant, setCheckedRelevant] = useState<any[]>([]); // For checkboxes
  const [checkedNonRelevant, setCheckedNonRelevant] = useState<any[]>([]); // For checkboxes

  // Handle create submit
  const onSubmit = (data: NewsTaskCreate) => {
    if (onCreate) {
      onCreate(data);
      reset();
    }
  };

  const checkNews = async (news: NewsTask) => {
    setCheckedRelevant([]); 
    setCheckedNonRelevant([]);
    if (news.relevant_news && news.relevant_news.length > 0) {
      const relevantResults = await Promise.all(
        news.relevant_news.map(async (item, index) => {
          const result = await newsTaskApi.checkRelevantNews(news.id, item);
          return { index, result };
        })
      );
      setCheckedRelevant(relevantResults);
    }
    if (news.non_relevant_news && news.non_relevant_news.length > 0) {
      const nonRelevantResults = await Promise.all(
        news.non_relevant_news.map(async (item, index) => {
          const result = await newsTaskApi.checkRelevantNews(news.id, item);
          return { index, result };
        })
      );
      console.log("Non-relevant results:", nonRelevantResults);
      setCheckedNonRelevant(nonRelevantResults);
    }
  };

const getCheckResult = (itemIndex: number, isRelevant: boolean) => {
  const checkedArray = isRelevant ? checkedRelevant : checkedNonRelevant;
  const found = checkedArray.find(item => item.index === itemIndex);
  return found ? found.result : null;
};

  const addNews = (isRelevant: boolean) => {
    let updatedTask = task;
    if (isRelevant && newRelevantNews.trim()) {
      updatedTask = {
        ...task,
        relevant_news: [...(task.relevant_news || []), newRelevantNews.trim()]
      };
      setTask(updatedTask);
    } else if (!isRelevant && newNonRelevantNews.trim()) {
      updatedTask = {
        ...task,
        non_relevant_news: [...(task.non_relevant_news || []), newNonRelevantNews.trim()]
      };
      setTask(updatedTask);
    }
    setNewRelevantNews(""); // Clear input
    setNewNonRelevantNews(""); // Clear input

    // Immediately save to backend
    if (onEdit) {
      onEdit(updatedTask);
    }
  };

  const removeNews = (news: string, isRelevant: boolean) => {
    const updatedTask = {
      ...task,
      relevant_news: isRelevant ? task.relevant_news?.filter((n) => n !== news) || [] : task.relevant_news,
      non_relevant_news: isRelevant ? task.non_relevant_news : task.non_relevant_news?.filter((n) => n !== news) || []
    };
    setTask(updatedTask);

    // Immediately save to backend
    if (onEdit) {
      onEdit(updatedTask);
    }
  };

  // Table list view
  if (listView && newsTask) {
    return (
      <Table.Row>
        <Table.Cell>
          <Text>{newsTask.title}</Text>
        </Table.Cell>
        <Table.Cell>
          <Text>{newsTask?.end_date ? new Date(newsTask.end_date).toLocaleDateString() : '∞'}</Text>
        </Table.Cell>
        {/* Buttons cell */}
        <Table.Cell>
          <Flex justifyContent="flex-end" gap={2}>
            <IconButton
              aria-label="Edit"
              size={"xs"}
              onClick={() => {
                setCurrentComponent(
                <NewsTaskCard
                  newsTask={newsTask}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  editMode={true}
                />)
              }}
            >
              <FiEdit2 />
            </IconButton>
              <IconButton
                aria-label="Active"
                colorScheme="green"
                size="xs"
                onClick={() => {
                    if (onEdit && newsTask) {
                      onEdit({
                        ...newsTask,
                        is_active: newsTask.is_active ? false : true 
                      });
                    }
                }}
              >
                {newsTask.is_active ? <FaPause /> : <FaPlay />}
              </IconButton>
              <IconButton
                aria-label="Delete"
                colorScheme="red"
                size="xs"
                onClick={() => {
                  if (newsTask && onDelete) {
                    onDelete(newsTask.id);
                  }
                }}
              >
            <MdDelete />
          </IconButton>
        </Flex>
        </Table.Cell>
      </Table.Row>
    )
  }

  return (
    <Box display="flex" flexDirection={"row"}>
    <Card.Root w={"600px"}>
      <Card.Body gap="2" position="relative">
        <Flex justify="space-between" align="start">
          <Box as="form" onSubmit={onCreate ? handleSubmit(onSubmit) : undefined} w="100%">
            <Card.Title marginBottom={2}>
                <Flex align="center" gap={2}>
                {onCreate ? (
                  <Input
                  placeholder="Enter task title"
                  {...register("title", { required: true })}
                  />
                ) : editMode ? (
                  <Input
                  value={task.title}
                  onChange={(e) => setTask({ ...task, title: e.target.value })}
                  />
                ) : (
                  <Flex align="center" gap={2}>
                    <Text flex={1}>{newsTask?.title}</Text>
                    <IconButton
                      aria-label="Copy title"
                      size="2xs"
                      onClick={() => {
                      if (newsTask?.link) {
                        navigator.clipboard.writeText(newsTask.link);
                      }
                      }}
                    >
                      <FaRegCopy />
                    </IconButton>
                  </Flex>
                )}
                </Flex>
            </Card.Title>
            <Card.Description>
              {onCreate ? (
                <Textarea
                  rows={3}
                  placeholder="Enter task description"
                  {...register("description", { required: true })}
                />
              ) : editMode ? (
                <Textarea
                  autoresize
                  placeholder="Edit task description"
                  value={task.description}
                  onChange={(e) => setTask({ ...task, description: e.target.value })}
                />
              ) : (
                newsTask?.description
              )}
            </Card.Description>
            {onCreate && (
              <>  
              <Input
                type="datetime-local"
                placeholder="End date"
                {...register("end_date", { required: true })}
                mt={2}
              />
              </>
            )}
          </Box>
        </Flex>
      </Card.Body>
      <Card.Footer p={4} gap={2}>
        <Stack>
        <Flex>
        {!onCreate && !editMode && newsTask && (
          <>
            <Text fontSize="sm" color="gray.500">
              Created at: {new Date(newsTask.created_at).toLocaleDateString()}
            </Text>
            <Text fontSize="sm" color="gray.500">
              End date: {new Date(newsTask.end_date).toLocaleDateString()}
            </Text>
          </>
        )}
        </Flex>
        <Flex justifyContent={"flex-end"} gap={2} mt={2}>
        {!onCreate && editMode && (
          <IconButton
            aria-label="Save"
            colorScheme="blue"
            size="xs"
            onClick={() => {
              if (onEdit) {
                onEdit(task);
              }
              setCurrentComponent(<AllTasks />);
            }}
          >
            <FiCheck />
          </IconButton>
        )}
        {onCreate && (
          <IconButton
            aria-label="Create"
            colorScheme="blue"
            size="xs"
            type="submit"
            form="form"
            onClick={handleSubmit(onSubmit)}
          >
            <FiCheck />
          </IconButton>
        )}

        {newsTask && (
          <IconButton
            aria-label="Active"
            colorScheme="green"
            size="xs"
            onClick={() => {
                if (onEdit && newsTask) {
                  onEdit({
                    ...newsTask,
                    is_active: newsTask.is_active ? false : true 
                  });
                }
            }}
          >
            {newsTask.is_active ? <FaPause /> : <FaPlay />}
          </IconButton>
        )}
        {!onCreate && (
          <>
          <IconButton
            aria-label="Delete"
            colorScheme="red"
            size="xs"
            onClick={() => {
              if (newsTask && onDelete) {
                onDelete(newsTask.id);
              }
            }}
          >
            <MdDelete />
          </IconButton>
          <IconButton
            aria-label="Check News"
            colorScheme="purple"
            size="xs"
            onClick={() => {
              if (newsTask) {
                checkNews(task);
              }
            }}
          >
            <MdRefresh />
          </IconButton>
          </>
          )
        }
        </Flex>
      </Stack>
      </Card.Footer>
    </Card.Root>
    {/* second column */}
    <Box display="flex" flexDirection="column" ml={2}>
      {onEdit && (
        <>
        <Text fontWeight="bold" mt={4}>Relevant News:</Text>
        {task?.relevant_news && (
          task.relevant_news.map((news, index) => {
            const checkResult = getCheckResult(index, true);
            return(
            <Box display="flex" flexDirection="row" alignItems="center" key={index} gap={2} mb={1}>
              <Text 
                key={index}
                fontSize={"xs"}
              >{news}</Text>
              <IconButton
                aria-label="Delete Relevant News"
                colorScheme="red"
                size="xs"
                onClick={() => removeNews(news, true)}
              >
                <MdDelete />
              </IconButton>
              {checkResult !== null && (
                <Box>
                  {checkResult ? (
                    <FaRegCheckCircle color="green" />
                  ) : (
                    <FaBan color="red" />
                  )}
                </Box>
              )}
              
            </Box>
          )})
        )}
        <Box display="flex" flexDirection="row">
          <Textarea placeholder="Add relevant news example" rows={3}
            value={newRelevantNews}
            onChange={(e) => setNewRelevantNews(e.target.value)}
          />
          <IconButton
            aria-label="Add Relevant News"
            colorScheme="green"
            size="sm"
            mt={2}
            ml={2}
            onClick={() => addNews(true)}
          >
            <FiCheck />
          </IconButton>
        </Box>
        <Text fontWeight="bold" mt={4}>Non Relevant News:</Text>
        {task?.non_relevant_news && (
          task.non_relevant_news.map((news, index) => {
            const checkResult = getCheckResult(index, false);
            return (
            <Box display="flex" flexDirection="row" alignItems="center" key={index} gap={2} mb={1}>
              <Text 
                key={index}
                fontSize={"xs"}
              >{news}</Text>
              <IconButton
                aria-label="Delete Non Relevant News"
                colorScheme="red"
                size="xs"
                onClick={() => removeNews(news, false)}
              >
                <MdDelete />
              </IconButton>
              {checkResult !== null && (
                <Box>
                  {!checkResult ? (
                    <FaRegCheckCircle color="green" />
                  ) : (
                    <FaBan color="red" />
                  )}
                </Box>
              )}
            </Box>
          )})
        )}
        <Box display="flex" flexDirection="row">
          <Textarea placeholder="Add non relevant news example" rows={3}
            value={newNonRelevantNews}
            onChange={(e) => setNewNonRelevantNews(e.target.value)}
          />
          <IconButton
            aria-label="Add Non Relevant News"
            colorScheme="green"
            size="sm"
            mt={2}
            ml={2}
            onClick={() => addNews(false)}
          >
            <FiCheck />
          </IconButton>
        </Box>
        </>
      )}
    </Box>
  </Box>
  );
}
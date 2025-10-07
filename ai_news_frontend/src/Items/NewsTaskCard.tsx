import { Card, Text, Box, Flex, IconButton, Input, Stack, Table } from "@chakra-ui/react";
import { Textarea } from "@chakra-ui/react";
import type { NewsTask, NewsTaskCreate } from "../interface";
import { FiEdit2, FiCheck } from "react-icons/fi";
import { FaPause, FaPlay } from "react-icons/fa";
import { MdDelete } from "react-icons/md";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { FaRegCopy } from "react-icons/fa";
import { useComponent } from "../hooks/Сomponent";
import AllTasks from "../Pages/Dashboard";


interface NewsTaskCardProps {
  newsTask?: NewsTask;
  onEdit?: (newsTask: NewsTask) => void;
  onCreate?: (newsTask: NewsTaskCreate) => void;
  onDelete?: (newsTaskId: number) => void;
  listView?: boolean;
  editMode?: boolean;
}

export default function NewsTaskCard({ newsTask, onEdit, onCreate, onDelete, listView, editMode }: NewsTaskCardProps) {
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
      link: ""
    },
  });

  // Local state for edit mode
  const [task, setTask] = useState<NewsTask>(newsTask || ({} as NewsTask));

  // Handle create submit
  const onSubmit = (data: NewsTaskCreate) => {
    if (onCreate) {
      onCreate(data);
      reset();
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
          )
        }
        </Flex>
      </Stack>
      </Card.Footer>
    </Card.Root>
  );
}
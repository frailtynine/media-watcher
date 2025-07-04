import { Card, Text, Box, Flex, IconButton, Input, Stack } from "@chakra-ui/react";
import { Textarea } from "@chakra-ui/react";
import type { NewsTask, NewsTaskCreate } from "../interface";
import { FiEdit2, FiCheck } from "react-icons/fi";
import { FaPause, FaPlay } from "react-icons/fa";
import { MdDelete } from "react-icons/md";
import { useState } from "react";
import { useForm } from "react-hook-form";

interface NewsTaskCardProps {
  newsTask?: NewsTask;
  onEdit?: (newsTask: NewsTask) => void;
  onCreate?: (newsTask: NewsTaskCreate) => void;
  onDelete?: (newsTaskId: number) => void;
}

export default function NewsTaskCard({ newsTask, onEdit, onCreate, onDelete }: NewsTaskCardProps) {
  const [isEditing, setIsEditing] = useState(false);

  // useForm for create mode
  const {
    register,
    handleSubmit,
    // formState: { errors },
    reset,
  } = useForm<NewsTaskCreate>({
    defaultValues: {
      title: "",
      description: "",
      end_date: "",
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

  return (
    <Card.Root w={"320px"}>
      <Card.Body gap="2" position="relative">
        <Flex justify="space-between" align="start">
          <Box as="form" onSubmit={onCreate ? handleSubmit(onSubmit) : undefined} w="100%">
            <Card.Title>
              {onCreate ? (
                <Input
                  placeholder="Enter task title"
                  {...register("title", { required: true })}
                />
              ) : isEditing ? (
                <Input
                  value={task.title}
                  onChange={(e) => setTask({ ...task, title: e.target.value })}
                />
              ) : (
                newsTask?.title
              )}
            </Card.Title>
            <Card.Description>
              {onCreate ? (
                <Textarea
                  rows={3}
                  placeholder="Enter task description"
                  {...register("description", { required: true })}
                />
              ) : isEditing ? (
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
              <Input
                type="datetime-local"
                placeholder="End date"
                {...register("end_date", { required: true })}
                mt={2}
              />
            )}
          </Box>
          {!onCreate && (
            <IconButton
              aria-label="Edit"
              position="absolute"
              top={2}
              right={2}
              size={"xs"}
              onClick={() => setIsEditing(true)}
            >
              <FiEdit2 />
            </IconButton>
          )}
        </Flex>
      </Card.Body>
      <Card.Footer p={4} gap={2}>
        <Stack>
        <Flex>
        {!onCreate && !isEditing && newsTask && (
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
        {!onCreate && isEditing && (
          <IconButton
            aria-label="Save"
            colorScheme="blue"
            size="xs"
            onClick={() => {
              if (onEdit) {
                onEdit(task);
              }
              setIsEditing(false);
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
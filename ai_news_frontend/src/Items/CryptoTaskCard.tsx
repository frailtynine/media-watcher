import { Card, Text, Box, Flex, IconButton, Input, Stack, NativeSelect, NumberInput, Field } from "@chakra-ui/react";
import { Textarea } from "@chakra-ui/react";
import type { CryptoTask, CryptoTaskCreate } from "../interface";
import { CryptoTaskType, CryptoTickersType } from "../interface";
import { FiEdit2, FiCheck } from "react-icons/fi";
import { FaPause, FaPlay } from "react-icons/fa";
import { MdDelete } from "react-icons/md";
import { useState } from "react";
import { useForm } from "react-hook-form";

interface CryptoTaskCardProps {
  cryptoTask?: CryptoTask;
  onEdit?: (cryptoTask: CryptoTask) => void;
  onCreate?: (cryptoTask: CryptoTaskCreate) => void;
  onDelete?: (cryptoTaskId: number) => void;
}
export default function CryptoTaskCard({ cryptoTask, onEdit, onCreate, onDelete }: CryptoTaskCardProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    reset,
  } = useForm<CryptoTaskCreate>({
    defaultValues: {
      title: "",
      description: "",
      end_date: "",
      end_point: 0.0,
      measurement_time: "22:00",
      ticker: CryptoTickersType.BTC,
      type: CryptoTaskType.PRICE
    },
  });

  const [task, setTask] = useState<CryptoTask>(cryptoTask || ({} as CryptoTask));

  const onSubmit = (data: CryptoTaskCreate) => {
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
                    cryptoTask?.title
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
                    cryptoTask?.description
                  )}
                </Card.Description>
                {onCreate && (
                  <>
                  <Field.Root>
                    <Field.Label>
                      End date:
                    </Field.Label>
                    <Input
                      type="datetime-local"
                      {...register("end_date", { required: true })}
                      mt={2}
                      />
                  </Field.Root>
                  <Field.Root>
                    <Field.Label>
                      Snapshot time:
                    </Field.Label>
                    <Input
                      type="time"
                      {...register("measurement_time", { required: true })}
                      mt={2}
                    />
                  </Field.Root>
                  <NativeSelect.Root>
                    <NativeSelect.Field
                      {...register("type", {required: true})}
                    >
                        {Object.values(CryptoTaskType).map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                        ))}
                      <NativeSelect.Indicator />
                    </NativeSelect.Field>
                  </NativeSelect.Root>
                      <NativeSelect.Root>
                    <NativeSelect.Field
                      {...register("ticker", {required: true})}
                    >
                        {Object.values(CryptoTickersType).map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                        ))}
                      <NativeSelect.Indicator />
                    </NativeSelect.Field>
                  </NativeSelect.Root>
                  <Field.Root>
                    <Field.Label>
                      Target price:
                    </Field.Label>
                    <NumberInput.Root defaultValue="0" width="200px">
                      <NumberInput.Control />
                      <NumberInput.Input
                        {...register("end_point", {
                          required: true
                        })}
                        step="0.1"
                      />
                    </NumberInput.Root>
                  </Field.Root>
                  </>
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
            {!onCreate && !isEditing && cryptoTask && (
              <>
                <Text fontSize="sm" color="gray.500">
                  Created at: {new Date(cryptoTask.created_at).toLocaleDateString()}
                </Text>
                <Text fontSize="sm" color="gray.500">
                  End date: {new Date(cryptoTask.end_date).toLocaleDateString()}
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
    
            {cryptoTask && (
              <IconButton
                aria-label="Active"
                colorScheme="green"
                size="xs"
                onClick={() => {
                    if (onEdit && cryptoTask) {
                      onEdit({
                        ...cryptoTask,
                        is_active: cryptoTask.is_active ? false : true 
                      });
                    }
                }}
              >
                {cryptoTask.is_active ? <FaPause /> : <FaPlay />}
              </IconButton>
            )}
            {!onCreate && (
              <IconButton
                aria-label="Delete"
                colorScheme="red"
                size="xs"
                onClick={() => {
                  if (cryptoTask && onDelete) {
                    onDelete(cryptoTask.id);
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
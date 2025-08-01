import { Text, Flex, IconButton, Table } from "@chakra-ui/react";
import { FaPause, FaPlay } from "react-icons/fa";
import type { Event } from "../interface";
import { MdDelete } from "react-icons/md";


interface EventProps {
  event: Event;
  onPause: (eventId: string) => void;
  listView?: boolean;
  onDelete: (eventId: string) => void;
}

export default function EventItem({ event, onPause, listView, onDelete }: EventProps) {

  if (listView) {
    return (
       <Table.Row>
        <Table.Cell>
          <Text>{event.title}</Text>
        </Table.Cell>
        <Table.Cell>
          <Text>{new Date(event.ends_at).toLocaleDateString()}</Text>
        </Table.Cell>
          {/* Buttons cell */}
        <Table.Cell>
          <Flex justifyContent="flex-end" gap={2}>
            <IconButton
              aria-label="Active"
              colorScheme="green"
              size="xs"
              onClick={() => {
                    onPause(event.id)
              }}
            >
              {event.is_active ? <FaPause /> : <FaPlay />}
            </IconButton>
            <IconButton
              aria-label="Delete"
              colorScheme="red"
              size="xs"
              onClick={() => {
                  onDelete(event.id);
                
              }}
            >
              <MdDelete />
            </IconButton>
          </Flex>
        </Table.Cell>
      </Table.Row>
    );
  }
}
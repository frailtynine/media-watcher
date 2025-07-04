import useWebSocket, { ReadyState} from "react-use-websocket";
import { useState, useEffect } from "react";
// import { authApi } from "../api";
import type { RedisMessage } from "../interface";
import { Table } from "@chakra-ui/react";


const MESSAGES_STORAGE_KEY = 'websocket_messages';
const MAX_MESSAGES = 100;

export default function LiveResults() {
  const url = "ws://localhost:8000/api/news_task/ws";
  const [messages, setMessages] = useState<RedisMessage[]>(() => {
    const savedMessages = localStorage.getItem(MESSAGES_STORAGE_KEY);
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  
  const { lastMessage, readyState } = useWebSocket(url, {
    shouldReconnect: () => true,
  });

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const parsedMessage = typeof lastMessage.data === 'string' 
          ? JSON.parse(lastMessage.data) 
          : lastMessage.data;

        if (parsedMessage && typeof parsedMessage === 'object') {
          const updatedMessages = (prev: RedisMessage[]) => {
            const updated = [...prev, parsedMessage];
            return updated.slice(-MAX_MESSAGES);
          };
          
          // Update state
          setMessages(updatedMessages);
          
          // Save to localStorage
          localStorage.setItem(
            MESSAGES_STORAGE_KEY, 
            JSON.stringify(updatedMessages(messages))
          );
        }
      } catch (error) {
        console.error('Error processing message:', error);
      }
    }
  }, [lastMessage]);

  
  return (
    <div>
      <h2>Live Results</h2>
      <div>
        WebSocket status: {ReadyState[readyState]}
      </div>
      <Table.Root striped size={"sm"}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>News Title</Table.ColumnHeader>
            <Table.ColumnHeader>Market</Table.ColumnHeader>
            <Table.ColumnHeader>Date</Table.ColumnHeader>
            <Table.ColumnHeader>Result</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
         {messages.length > 0 && [...messages].reverse().map((msg, idx) => (
            <Table.Row key={idx}>
              <Table.Cell>
                {msg?.news?.title ? (
                  <a href={msg.news.link || '#'} target="_blank" rel="noopener noreferrer">
                    {msg.news.title}
                  </a>
                ) : (
                  "No title available"
                )}
              </Table.Cell>
              <Table.Cell>{msg?.task?.title || "Unknown"}</Table.Cell>
              <Table.Cell>
                {msg?.news?.pub_date 
                  ? new Date(msg.news.pub_date).toLocaleString() 
                  : "Unknown date"
                }
              </Table.Cell>
              <Table.Cell>
                {msg?.task?.result !== undefined 
                  ? (msg.task.result ? "True" : "False") 
                  : "Unknown"
                }
              </Table.Cell>
            </Table.Row>  
          ))}
        </Table.Body>
      </Table.Root>
    </div>
  );

}
import { Box, Button, Text, Input, List, Field } from "@chakra-ui/react";
import { newsTaskApi } from "../api";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import type { Sources } from "../interface";

export default function SourcesComponent(props: { sources: Sources, taskId: number }) {
  const { sources, taskId } = props;
  const { setValue, control } = useForm<Sources>();
  const tgUrls = useWatch({
      control,
      name: "tg_urls",
      defaultValue: { ...sources.tg_urls}
    });
  
    const rssUrls = useWatch({
      control,
      name: "rss_urls",
      defaultValue: { ...sources.rss_urls}
    });
    const [validating, setValidating] = useState({ 
      isLoadingTG: false, messageTg: "", errorTg: "" 
    , isLoadingRss: false, messageRss: "", errorRss: "" });
  
    function recordToList(record: Record<string, string> | undefined) {
      if (!record) return [];
      return Object.entries(record).map(([key, value]) => ({ key, value }));
    }
    const tgUrlsList = recordToList(tgUrls);
    const rssUrlsList = recordToList(rssUrls);
    

  const handleSetValidating = (listName: "tg_urls" | "rss_urls", isLoading: boolean, message: string, error: string) => {
    if (listName === "tg_urls") {
      setValidating({ ...validating, isLoadingTG: isLoading, messageTg: message, errorTg: error });
    } else {
      setValidating({ ...validating, isLoadingRss: isLoading, messageRss: message, errorRss: error });
    }
  };


  const handleAddToList = async (listName: "tg_urls" | "rss_urls", item: { key: string; value: string }) => {
    const currentList = listName === "tg_urls" ? tgUrlsList : rssUrlsList;
    const updatedList = [...currentList, item];
    // convert array of {key,value} back to a record expected by the form
    const updatedRecord = Object.fromEntries(updatedList.map(({ key, value }) => [key, value])) as Record<string, string>;
    handleSetValidating(listName, true, "Validating...", "");
    const sourceType = listName === "tg_urls" ? "telegram" : "rss";
  
    await newsTaskApi.customCall("POST", "add_source", {
      source_url: item.value,
      source_name: item.key,
      source_type: sourceType,
      task_id: taskId
    }).then((data) => {
      console.log("Validation response:", data);
      if (data.status === 200) {
        setValue(listName, updatedRecord);
        handleSetValidating(listName, false, "", "");
      }
    }).catch((error) => {
      console.error("Error validating URL:", error);
      handleSetValidating(listName, false, "", error.response.data.detail);
    });
  };

  const removeFromList = async (listName: "tg_urls" | "rss_urls", item: { key: string; value: string }) => {
    const currentList = listName === "tg_urls" ? tgUrlsList : rssUrlsList;
    const updatedList = currentList.filter(({ key }) => key !== item.key);
    // convert array of {key,value} back to a record expected by the form
    const updatedRecord = Object.fromEntries(updatedList.map(({ key, value }) => [key, value])) as Record<string, string>;
    
    handleSetValidating(listName, true, "Removing...", "");
    const sourceType = listName === "tg_urls" ? "telegram" : "rss";
    await newsTaskApi.customCall("DELETE", "remove_source", {
      source_name: item.key,
      source_type: sourceType,
      source_url: item.value,
      task_id: taskId
    }).then((data) => {
      console.log("Remove response:", data);
      if (data) {
        setValue(listName, updatedRecord);
        handleSetValidating(listName, false, "", "");
      }
    }).catch((error) => {
      console.error("Error removing source:", error);
      handleSetValidating(listName, false, "", error.response?.data?.detail || "Failed to remove source");
    });
  };
  
  const SourcesList = ({ listName }: { listName: "tg_urls" | "rss_urls" }) => {
    const rss_key = listName === "tg_urls" ? "tg_key" : "rss_key";
    const rss_value = listName === "tg_urls" ? "tg_value" : "rss_value";
    return (
      <Box mb={6}>
        <Box display="flex" alignItems="flex-start" gap={3} mb={4}>
          <Box flex="1">
            <Field.Root invalid={!!(listName === "tg_urls" ? validating.errorTg : validating.errorRss)}>
              <Input placeholder="URL" id={rss_value} required />
              <Field.ErrorText mt={1}>{listName === "tg_urls" ? validating.errorTg : validating.errorRss}</Field.ErrorText>
            </Field.Root>
          </Box>
          <Box w="150px">
            <Input placeholder="Name" id={rss_key} required />
          </Box>
          <Button 
            size="sm" 
            onClick={() => {
              const keyInput = document.getElementById(rss_key) as HTMLInputElement;
              const valueInput = document.getElementById(rss_value) as HTMLInputElement;
              if (keyInput.value && valueInput.value) {
                handleAddToList(listName, { key: keyInput.value, value: valueInput.value });
                keyInput.value = "";
                valueInput.value = "";
              }
            }}
            loading={listName === "tg_urls" ? validating.isLoadingTG : validating.isLoadingRss}
            loadingText={listName === "tg_urls" ? validating.messageTg : validating.messageRss}
            minW="80px"
          >
            Add
          </Button>
        </Box>
        <List.Root>
          {(listName === "tg_urls" ? tgUrlsList : rssUrlsList).map(({ key, value }) => (
            <List.Item key={key} display="flex" alignItems="center" justifyContent="space-between" p={3} mb={2} borderWidth={1} borderRadius="md" bg="gray.50">
              <Text><a href={value} target="_blank" rel="noopener noreferrer">{key}</a></Text>
              <Button size="sm" colorScheme="red" onClick={() => removeFromList(listName, { key, value})}>Remove</Button>
            </List.Item>
          ))}
        </List.Root>
      </Box>
    );
  };

  return (
    <Box>
      <Text fontSize="xl" fontWeight="bold" mb={4}>Telegram</Text>
      <SourcesList listName="tg_urls" />
      <Text fontSize="xl" fontWeight="bold" mb={4}>RSS</Text>
      <SourcesList listName="rss_urls" />
    </Box>
  );
};
import { Box, Heading, Button, Textarea, Text, Input, List } from "@chakra-ui/react";
import { useEffect } from "react";
import type { Prompt, Settings } from "../interface";
import { promptApi, settingsAPI } from "../api";
import { useForm, useWatch } from "react-hook-form";

type SettingsFormData = Prompt & Settings;

export default function Settings() {
  const { register, handleSubmit, reset, getValues, setValue, control } = useForm<SettingsFormData>();
  const tgUrls = useWatch({
    control,
    name: "tg_urls",
    defaultValue: {}
  });

  const rssUrls = useWatch({
    control,
    name: "rss_urls",
    defaultValue: {}
  });

  function recordToList(record: Record<string, string> | undefined) {
    if (!record) return [];
    return Object.entries(record).map(([key, value]) => ({ key, value }));
  }
  const tgUrlsList = recordToList(tgUrls);
  const rssUrlsList = recordToList(rssUrls);



  useEffect(() => {
    const fetchAllSettings = async () => {
      const [promptData, appData] = await Promise.all([
        promptApi.getPrompt(),
        settingsAPI.getSettings()
      ]);

      if (promptData || appData) {
        // Reset form with all values at once
        reset({
          ...(promptData),
          ...(appData)
        });
      }
    };

    fetchAllSettings();
  }, [reset]);

  const handleSavePrompt = async (formData: SettingsFormData) => {
    const updated = await promptApi.updatePrompt(formData);
    reset({
      ...getValues(),
      ...updated
    });
  };

  const handleSaveSettings = async (formData: SettingsFormData) => {
    const updatedSettings = await settingsAPI.updateSettings(formData);
    reset({
      ...getValues(),
      ...updatedSettings
    });
  }

  const handleResetDefaults = async () => {
    const settings = await promptApi.customCall("POST", "reset");
    reset({
      ...getValues(),
      ...settings
    });
  };

  const handleAddToList = (listName: "tg_urls" | "rss_urls", item: { key: string; value: string }) => {
    const currentList = listName === "tg_urls" ? tgUrlsList : rssUrlsList;
    const updatedList = [...currentList, item];
    // convert array of {key,value} back to a record expected by the form
    const updatedRecord = Object.fromEntries(updatedList.map(({ key, value }) => [key, value])) as Record<string, string>;
    if (listName === "tg_urls") {
      setValue("tg_urls", updatedRecord);
    } else {
      setValue("rss_urls", updatedRecord);
    }
  };

  const removeFromList = (listName: "tg_urls" | "rss_urls", keyToRemove: string) => {
    const currentList = listName === "tg_urls" ? tgUrlsList : rssUrlsList;
    const updatedList = currentList.filter(({ key }) => key !== keyToRemove);
    // convert array of {key,value} back to a record expected by the form
    const updatedRecord = Object.fromEntries(updatedList.map(({ key, value }) => [key, value])) as Record<string, string>;
    if (listName === "tg_urls") {
      setValue("tg_urls", updatedRecord);
    } else {
      setValue("rss_urls", updatedRecord);
    }
  };

  const SourcesList = ({ listName }: { listName: "tg_urls" | "rss_urls" }) => {
    const rss_key = listName === "tg_urls" ? "tg_key" : "rss_key";
    const rss_value = listName === "tg_urls" ? "tg_value" : "rss_value";
    return (
      <>
      <Box display="flex" alignItems="center" mb={4}>
        <Input placeholder="Url" id={rss_value} w={"200px"} mr={2} required/>
        <Input placeholder="Name" id={rss_key} w={"70px"} required/>
        <Button size="sm" ml={2} onClick={() => {
          const keyInput = document.getElementById(rss_key) as HTMLInputElement;
          const valueInput = document.getElementById(rss_value) as HTMLInputElement;
          if (keyInput.value && valueInput.value) {
            handleAddToList(listName, { key: keyInput.value, value: valueInput.value });
            keyInput.value = "";
            valueInput.value = "";
          }
        }}>
          Add
        </Button>
      </Box>
      <List.Root>
        {(listName === "tg_urls" ? tgUrlsList : rssUrlsList).map(({ key, value }) => (
          <List.Item key={key} display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Text><a href={value} target="_blank" rel="noopener noreferrer">{key}</a></Text>
            <Button size="sm" colorScheme="red" onClick={() => removeFromList(listName, key)}>Remove</Button>
          </List.Item>
        ))}
      </List.Root>
      </>
    );
  };


  return (
    <Box p={6} maxW="800px" mx="auto">
      <Heading mb={4} color="gray.700">Settings</Heading>
        <Box p={4} borderWidth={1} borderRadius="md" mb={6}>
          <Text mb={2} fontWeight="semibold">System Role:</Text>
          <Textarea rows={5} {...register("role")} mb={4} />
          <Button mt={4} onClick={handleSubmit(handleSavePrompt)} colorScheme="blue">
            Save Prompt
          </Button>
          <Button mt={4} ml={4} onClick={handleResetDefaults} variant="outline">
            Reset to Defaults
          </Button>
        </Box>
        <Box display={"flex"} flexDirection={"column"} mt={8} p={4} borderWidth={1} borderRadius="md">
          <Text mb={4} fontWeight="semibold" fontSize="lg">Telegram URLs:</Text>
          <SourcesList listName="tg_urls"/>
          <Text mb={4} fontWeight="semibold" fontSize="lg">RSS URLs:</Text>
          <SourcesList listName="rss_urls"/>
        </Box>
        <Box p={4} borderWidth={1} borderRadius="md" mt={6}>
          <Text mb={2} fontWeight="semibold">Deepseek API Key:</Text>
          <Input {...register("deepseek")} mb={4} w={"200px"} type="password"/>
          <Text mb={2} fontWeight="semibold">Deepl API Key:</Text>
          <Input {...register("deepl")} mb={4} w={"200px"} type="password"/>
          <Button mt={4} ml={4} onClick={handleSubmit(handleSaveSettings)} w={"100px"} colorScheme="green">
            Save Settings
          </Button>
        </Box>

    </Box>
  );
}

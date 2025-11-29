import { Box, Heading, Button, Textarea, Text, Input } from "@chakra-ui/react";
import { useEffect } from "react";
import type { Prompt, Settings } from "../interface";
import { promptApi, settingsAPI } from "../api";
import { useForm } from "react-hook-form";

type SettingsFormData = Prompt & Settings;

export default function Settings() {
  const { register, handleSubmit, reset, getValues } = useForm<SettingsFormData>();



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
    const data = {
      deepseek: formData.deepseek,
    }
    const updatedSettings = await settingsAPI.updateSettings(data);
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


  return (
    <Box p={6} maxW="900px" mx="auto">
      <Heading mb={6} color="gray.700" size="xl">Settings</Heading>

      <Box p={6} borderWidth={1} borderRadius="lg" mb={6} bg="white" shadow="sm">
        <Text mb={4} fontWeight="semibold" fontSize="lg" color="gray.800">System Role</Text>
        <Textarea rows={10} {...register("role")} mb={6} />
        <Box display="flex" gap={3}>
          <Button onClick={handleSubmit(handleSavePrompt)} colorScheme="blue">
            Save Prompt
          </Button>
          <Button onClick={handleResetDefaults} variant="outline">
            Reset to Defaults
          </Button>
        </Box>
      </Box>

      <Box p={6} borderWidth={1} borderRadius="lg" bg="white" shadow="sm">
        <Text mb={6} fontWeight="semibold" fontSize="lg" color="gray.800">Gemini API key:</Text>
        <Box display="flex" flexDirection="column" gap={4}>
          <Box>
            <Input {...register("deepseek")} type="password" maxW="300px" />
          </Box>
          <Box mt={4}>
            <Button onClick={handleSubmit(handleSaveSettings)} colorScheme="green">
              Save key
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

import { Box, Heading, Button, Textarea, Text } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import type { Prompt } from "../interface";
import { promptApi } from "../api";
import { set, useForm } from "react-hook-form";


export default function Settings() {
  const [promptSettings, setPromptSettings] = useState<Prompt | null>(null);
  const { register, handleSubmit, setValue } = useForm<Prompt>();

  useEffect(() => {
    const fetchPromptSettings = async () => {
      await promptApi.getPrompt().then((settings) => {
        setPromptSettings(settings || null);
        if (settings) {
          setValue("role", settings.role);
          setValue("crypto_role", settings.crypto_role);
          setValue("suggest_post", settings.suggest_post);
          setValue("post_examples", settings.post_examples);
        }
      });
    };

    fetchPromptSettings();
  }, [setValue]);

  const handleSaveSettings = async (formData: Prompt) => {
    if (promptSettings) {
      formData.id = promptSettings.id;
      await promptApi.update(promptSettings.id, formData).then((updated) => {
        setPromptSettings(updated);
      });
    }
  };

  const handleResetDefaults = async () => {
    await promptApi.customCall('POST', 'reset').then((settings) => {
      setPromptSettings(settings || null);
    });
  };

  return (
    <Box>
      <Heading mb={4}>Settings</Heading>
      {promptSettings && (
        <Box>
          <Text mb={2}>System Role:</Text>
          <Textarea
            rows={5}
            {...register("role")}
          />
          <Text mb={2}>Crypto Role:</Text>
          <Textarea
            rows={5}
            {...register("crypto_role")}
          />
          <Text mb={2}>Suggested Post:</Text>
          <Textarea
            rows={5}
            {...register("suggest_post")}
          />
          <Button mt={4} onClick={handleSubmit(handleSaveSettings)}>
            Save Settings
          </Button>
          <Button mt={4} ml={4} onClick={handleResetDefaults}>
            Reset to Defaults
          </Button>
        </Box>
      )}
    </Box>
  );
}

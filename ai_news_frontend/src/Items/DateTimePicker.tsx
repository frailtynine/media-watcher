import React, { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Input,
  Text,
} from '@chakra-ui/react';

interface DateTimePickerProps {
  value?: Date;
  onChange?: (date: Date) => void;
  showTimeSelect?: boolean;
  placeholder?: string;
}

const DateTimePicker: React.FC<DateTimePickerProps> = ({
  value = new Date(),
  onChange,
  showTimeSelect = true,
  placeholder = "Select date and time",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date>(value);
  const [hours, setHours] = useState<number>(value.getHours());
  const [minutes, setMinutes] = useState<number>(value.getMinutes());
  
  // Format the date for display in the input
  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    
    if (showTimeSelect) {
      return `${year}-${month}-${day} ${hour}:${minute}`;
    }
    return `${year}-${month}-${day}`;
  };

  const toggleOpen = () => setIsOpen(!isOpen);
  
  // Simplified version that just uses a basic input
  return (
    <Box>
      <Button onClick={toggleOpen} variant="outline" width="100%">
        {selectedDate ? formatDate(selectedDate) : placeholder}
      </Button>
      
      {isOpen && (
        <Box 
          position="absolute" 
          zIndex={10} 
          bg="white" 
          boxShadow="md" 
          borderRadius="md"
          p={4}
          mt={2}
          border="1px solid"
          borderColor="gray.200"
        >
          <Flex direction="column" gap={2}>
            <Input 
              type="date" 
              value={`${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`}
              onChange={(e) => {
                const date = new Date(e.target.value);
                if (!isNaN(date.getTime())) {
                  const newDate = new Date(
                    date.getFullYear(),
                    date.getMonth(),
                    date.getDate(),
                    hours,
                    minutes
                  );
                  setSelectedDate(newDate);
                  
                  if (onChange) {
                    onChange(newDate);
                  }
                }
              }}
            />
            
            {showTimeSelect && (
              <Flex gap={2} align="center">
                <Input
                  type="number"
                  min={0}
                  max={23}
                  value={hours}
                  onChange={(e) => {
                    const newHours = parseInt(e.target.value);
                    setHours(newHours);
                    
                    const newDate = new Date(
                      selectedDate.getFullYear(),
                      selectedDate.getMonth(),
                      selectedDate.getDate(),
                      newHours,
                      minutes
                    );
                    
                    setSelectedDate(newDate);
                    
                    if (onChange) {
                      onChange(newDate);
                    }
                  }}
                  size="sm"
                  width="60px"
                />
                <Text>:</Text>
                <Input
                  type="number"
                  min={0}
                  max={59}
                  value={minutes}
                  onChange={(e) => {
                    const newMinutes = parseInt(e.target.value);
                    setMinutes(newMinutes);
                    
                    const newDate = new Date(
                      selectedDate.getFullYear(),
                      selectedDate.getMonth(),
                      selectedDate.getDate(),
                      hours,
                      newMinutes
                    );
                    
                    setSelectedDate(newDate);
                    
                    if (onChange) {
                      onChange(newDate);
                    }
                  }}
                  size="sm"
                  width="60px"
                />
              </Flex>
            )}
            
            <Button 
              colorScheme="blue" 
              onClick={() => {
                setIsOpen(false);
                if (onChange) {
                  onChange(selectedDate);
                }
              }}
              mt={2}
            >
              Confirm
            </Button>
          </Flex>
        </Box>
      )}
    </Box>
  );
};

export default DateTimePicker;

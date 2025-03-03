import React, { useState } from 'react';
import {
  Box,
  Button,
  VStack,
  FormControl,
  FormLabel,
  Input,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  useToast,
} from '@chakra-ui/react';

export const StrategyControls: React.FC = () => {
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const toast = useToast();

  const handleStart = async () => {
    setIsStarting(true);
    try {
      const response = await fetch('http://localhost:8000/api/strategy/start', {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Strategy Started',
          status: 'success',
          duration: 3000,
        });
      } else {
        throw new Error('Failed to start strategy');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to start strategy',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsStarting(false);
    }
  };

  const handleStop = async () => {
    setIsStopping(true);
    try {
      const response = await fetch('http://localhost:8000/api/strategy/stop', {
        method: 'POST',
      });
      
      if (response.ok) {
        toast({
          title: 'Strategy Stopped',
          status: 'info',
          duration: 3000,
        });
      } else {
        throw new Error('Failed to stop strategy');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to stop strategy',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsStopping(false);
    }
  };

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" w="100%">
      <VStack spacing={4}>
        <FormControl>
          <FormLabel>Risk per Trade (%)</FormLabel>
          <NumberInput defaultValue={1} min={0.1} max={5} step={0.1}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <FormControl>
          <FormLabel>Max Drawdown (%)</FormLabel>
          <NumberInput defaultValue={20} min={5} max={50} step={1}>
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>

        <Button
          colorScheme="green"
          isLoading={isStarting}
          onClick={handleStart}
          w="100%"
        >
          Start Strategy
        </Button>

        <Button
          colorScheme="red"
          isLoading={isStopping}
          onClick={handleStop}
          w="100%"
        >
          Stop Strategy
        </Button>
      </VStack>
    </Box>
  );
};

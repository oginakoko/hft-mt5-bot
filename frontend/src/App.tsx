import React, { useEffect, useState } from 'react';
import {
  ChakraProvider,
  Box,
  VStack,
  Grid,
  theme,
} from '@chakra-ui/react';
import { PerformanceMetrics } from './components/PerformanceMetrics';
import { AccountInfo } from './components/AccountInfo';
import { TradeLog } from './components/TradeLog';
import { StrategyControls } from './components/StrategyControls';

export const App = () => {
  const [status, setStatus] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws/performance');
    ws.onmessage = (event) => {
      setMetrics(JSON.parse(event.data));
    };

    // Fetch initial status
    fetch('http://localhost:8000/api/status')
      .then(res => res.json())
      .then(data => setStatus(data));

    return () => ws.close();
  }, []);

  return (
    <ChakraProvider theme={theme}>
      <Box textAlign="center" fontSize="xl">
        <Grid minH="100vh" p={3}>
          <VStack spacing={8}>
            <PerformanceMetrics metrics={metrics} />
            <AccountInfo status={status} />
            <TradeLog />
            <StrategyControls />
          </VStack>
        </Grid>
      </Box>
    </ChakraProvider>
  );
};

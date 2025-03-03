import React, { useEffect, useState } from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Heading,
  useColorModeValue,
} from '@chakra-ui/react';

interface Trade {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  openTime: string;
  openPrice: number;
  stopLoss: number;
  takeProfit: number;
  profit: number;
}

export const TradeLog: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/trades');
    
    ws.onmessage = (event) => {
      const newTrades = JSON.parse(event.data);
      setTrades(newTrades);
    };

    return () => ws.close();
  }, []);

  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" w="100%" bg={bgColor}>
      <Heading size="md" mb={4}>Trade Log</Heading>
      
      <Table variant="simple" size="sm">
        <Thead>
          <Tr>
            <Th>Ticket</Th>
            <Th>Symbol</Th>
            <Th>Type</Th>
            <Th>Volume</Th>
            <Th>Open Price</Th>
            <Th>Profit</Th>
          </Tr>
        </Thead>
        <Tbody>
          {trades.map((trade) => (
            <Tr key={trade.ticket}>
              <Td>{trade.ticket}</Td>
              <Td>{trade.symbol}</Td>
              <Td>
                <Badge colorScheme={trade.type === 'BUY' ? 'green' : 'red'}>
                  {trade.type}
                </Badge>
              </Td>
              <Td isNumeric>{trade.volume.toFixed(2)}</Td>
              <Td isNumeric>{trade.openPrice.toFixed(5)}</Td>
              <Td 
                isNumeric 
                color={trade.profit >= 0 ? 'green.500' : 'red.500'}
              >
                ${trade.profit.toFixed(2)}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
};

import React from 'react';
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
} from '@chakra-ui/react';

interface AccountInfoProps {
  status: {
    status: string;
    account_info: {
      balance: number;
      equity: number;
      margin: number;
      free_margin: number;
      profit: number;
    };
    active_symbols: string[];
    positions: number;
  } | null;
}

export const AccountInfo: React.FC<AccountInfoProps> = ({ status }) => {
  if (!status) return null;

  const { account_info, active_symbols, positions } = status;

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" w="100%">
      <Heading size="md" mb={4}>Account Information</Heading>
      <Badge colorScheme={status.status === 'running' ? 'green' : 'red'} mb={4}>
        {status.status.toUpperCase()}
      </Badge>
      
      <Table variant="simple" size="sm">
        <Tbody>
          <Tr>
            <Th>Balance</Th>
            <Td isNumeric>${account_info.balance.toFixed(2)}</Td>
          </Tr>
          <Tr>
            <Th>Equity</Th>
            <Td isNumeric>${account_info.equity.toFixed(2)}</Td>
          </Tr>
          <Tr>
            <Th>Profit</Th>
            <Td isNumeric color={account_info.profit >= 0 ? 'green.500' : 'red.500'}>
              ${account_info.profit.toFixed(2)}
            </Td>
          </Tr>
          <Tr>
            <Th>Open Positions</Th>
            <Td isNumeric>{positions}</Td>
          </Tr>
          <Tr>
            <Th>Active Symbols</Th>
            <Td>{active_symbols.join(', ')}</Td>
          </Tr>
        </Tbody>
      </Table>
    </Box>
  );
};

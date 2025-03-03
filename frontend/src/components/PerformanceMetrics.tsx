import React from 'react';
import {
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  StatGroup,
  Box,
} from '@chakra-ui/react';

interface Props {
  metrics: any;
}

export const PerformanceMetrics: React.FC<Props> = ({ metrics }) => {
  if (!metrics) return null;

  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg">
      <StatGroup>
        <Stat>
          <StatLabel>Trades/sec</StatLabel>
          <StatNumber>{metrics.trades_per_second.toFixed(2)}</StatNumber>
          <StatHelpText>
            <StatArrow type="increase" />
            {metrics.execution_latency}ms latency
          </StatHelpText>
        </Stat>

        <Stat>
          <StatLabel>Drawdown</StatLabel>
          <StatNumber>{(metrics.drawdown * 100).toFixed(2)}%</StatNumber>
          <StatHelpText>
            Peak drawdown: {(metrics.peak_drawdown * 100).toFixed(2)}%
          </StatHelpText>
        </Stat>

        <Stat>
          <StatLabel>Signal Rate</StatLabel>
          <StatNumber>{metrics.signals_per_second.toFixed(2)}/s</StatNumber>
        </Stat>
      </StatGroup>
    </Box>
  );
};

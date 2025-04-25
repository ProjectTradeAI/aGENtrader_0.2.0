import React from 'react';
import { 
  LineChart as RechartLine, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer,
  PieChart as RechartPie,
  Pie,
  Cell
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

interface LineChartProps {
  data: Array<{
    date: string;
    value: number;
  }>;
  xKey?: string;
  yKey?: string;
  color?: string;
}

interface PieChartProps {
  data: Array<{
    name: string;
    value: number;
  }>;
}

export function LineChart({ 
  data, 
  xKey = 'date', 
  yKey = 'value', 
  color = '#0088FE' 
}: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartLine
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey={yKey} 
          stroke={color} 
          activeDot={{ r: 8 }}
        />
      </RechartLine>
    </ResponsiveContainer>
  );
}

export function PieChart({ data }: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartPie>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          fill="#8884d8"
          paddingAngle={5}
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </RechartPie>
    </ResponsiveContainer>
  );
}
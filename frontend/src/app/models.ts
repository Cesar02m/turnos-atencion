export interface Ticket {
  id: number;
  code: string;
  status: 'waiting' | 'serving' | 'done';
  counter: number | null;
  createdAt: string;
}

export interface Counter {
  id: number;
  name: string;
  status: 'available' | 'busy';
  ticket: Ticket | null;
}

export interface Dashboard {
  tickets: Ticket[];
  counters: Counter[];
  nextTicket: Ticket | null;
  stats: { waiting: number; served: number; available: number };
}

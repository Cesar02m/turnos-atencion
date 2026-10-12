import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Dashboard, Ticket } from './models';

@Injectable({ providedIn: 'root' })
export class QueueService {
  constructor(private readonly http: HttpClient) {}

  getDashboard(): Observable<Dashboard> {
    return this.http.get<Dashboard>('/api/dashboard');
  }

  createTicket(): Observable<Ticket> {
    return this.http.post<Ticket>('/api/tickets', {});
  }

  callNext(counterId: number): Observable<Dashboard> {
    return this.http.post<Dashboard>(`/api/counters/${counterId}/call`, {});
  }

  finish(counterId: number): Observable<Dashboard> {
    return this.http.post<Dashboard>(`/api/counters/${counterId}/finish`, {});
  }
}

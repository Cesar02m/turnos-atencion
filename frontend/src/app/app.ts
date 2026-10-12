import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { QueueService } from './queue.service';
import { Counter, Dashboard, Ticket } from './models';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.html',
})
export class AppComponent implements OnInit, OnDestroy {
  view: 'cliente' | 'operador' = 'cliente';
  readonly averageServiceMinutes = 8;
  dashboard: Dashboard = { tickets: [], counters: [], nextTicket: null, stats: { waiting: 0, served: 0, available: 0 } };
  loading = true;
  busyAction = false;
  notice = '';
  now = new Date();
  private pollId?: number;
  private clockId?: number;
  private lastCalled = '';
  private audio?: AudioContext;

  constructor(private readonly queue: QueueService) {}

  get currentCall(): Ticket | null {
    return this.dashboard.counters.find(counter => counter.ticket)?.ticket ?? null;
  }

  counterFor(ticket: Ticket): string {
    return this.dashboard.counters.find(counter => counter.ticket?.id === ticket.id)?.name ?? 'la ventanilla indicada';
  }

  ngOnInit(): void {
    this.view = new URLSearchParams(window.location.search).get('vista') === 'operador' ? 'operador' : 'cliente';
    this.refresh();
    this.pollId = window.setInterval(() => this.refresh(), 2500);
    this.clockId = window.setInterval(() => this.now = new Date(), 30_000);
  }

  ngOnDestroy(): void {
    window.clearInterval(this.pollId);
    window.clearInterval(this.clockId);
    this.audio?.close();
  }

  refresh(): void {
    this.queue.getDashboard().subscribe({
      next: value => {
        const call = value.counters.find(counter => counter.ticket)?.ticket;
        if (call && call.code !== this.lastCalled) {
          this.lastCalled = call.code;
          if (!this.loading) this.playChime();
        }
        this.dashboard = value;
        this.loading = false;
      },
      error: () => { this.loading = false; this.notice = 'No se pudo conectar con el servidor.'; },
    });
  }

  createTicket(): void {
    this.busyAction = true;
    this.queue.createTicket().subscribe({
      next: ticket => { this.notice = `Tu turno ${ticket.code} está listo.`; this.busyAction = false; this.refresh(); },
      error: error => { this.notice = error.error?.error ?? 'No se pudo generar el turno.'; this.busyAction = false; },
    });
  }

  callNext(counter: Counter): void {
    this.busyAction = true;
    this.queue.callNext(counter.id).subscribe({
      next: value => { this.dashboard = value; this.lastCalled = value.counters.find(item => item.id === counter.id)?.ticket?.code ?? this.lastCalled; this.playChime(); this.notice = `${counter.name}: pase ${this.lastCalled || 'el siguiente turno'}.`; this.busyAction = false; },
      error: error => { this.notice = error.error?.error ?? 'No hay turnos disponibles.'; this.busyAction = false; },
    });
  }

  finish(counter: Counter): void {
    this.busyAction = true;
    this.queue.finish(counter.id).subscribe({
      next: value => { this.dashboard = value; this.notice = `${counter.name} está disponible.`; this.busyAction = false; },
      error: error => { this.notice = error.error?.error ?? 'No se pudo cerrar la atención.'; this.busyAction = false; },
    });
  }

  get waitingTickets(): Ticket[] { return this.dashboard.tickets.filter(ticket => ticket.status === 'waiting'); }
  estimatedWait(counter: Counter): number {
    if (counter.status === 'busy') return this.averageServiceMinutes;
    const available = Math.max(this.dashboard.stats.available, 1);
    return this.waitingTickets.length ? Math.ceil(this.waitingTickets.length / available) * this.averageServiceMinutes : 0;
  }
  formatTime(value: string): string { return new Date(value).toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' }); }

  private playChime(): void {
    try {
      this.audio ??= new AudioContext();
      const oscillator = this.audio.createOscillator();
      const gain = this.audio.createGain();
      oscillator.connect(gain); gain.connect(this.audio.destination);
      oscillator.frequency.value = 740; gain.gain.setValueAtTime(0.001, this.audio.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.18, this.audio.currentTime + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audio.currentTime + 0.55);
      oscillator.start(); oscillator.stop(this.audio.currentTime + 0.56);
    } catch { /* El navegador puede bloquear audio antes de la primera interacción. */ }
  }
}


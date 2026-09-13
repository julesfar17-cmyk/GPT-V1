/* Shared audio clock for tap tools. One source spans pre-roll and excerpt:
   scheduling never depends on the visual countdown's timers. */
window.BeatTapAudio = class BeatTapAudio {
  constructor({context, buffer, start, duration, rate = 1, countdown = 3,
    onCount = () => {}, onRun = () => {}, onTick = () => {}, onEnd = () => {}}) {
    Object.assign(this, {context, buffer, startOffset:start, duration, rate, countdown,
      onCount, onRun, onTick, onEnd});
    this.closed = false; this.running = false; this.raf = 0; this.endTimer = 0;
  }
  async start() {
    await this.context.resume();
    if (this.closed) return false;
    if (this.context.state !== 'running') throw new Error('Audio indisponible — relance la prise.');
    if (!(this.duration > 0) || this.startOffset < 0 || this.startOffset >= this.buffer.duration)
      throw new Error('Extrait audio invalide.');
    this.duration = Math.min(this.duration, this.buffer.duration - this.startOffset);
    this.latency = Math.max(0, this.context.outputLatency || this.context.baseLatency || 0);
    const lead = 0.04, pre = Math.min(this.startOffset, this.countdown * this.rate);
    this.sourceOffset = this.startOffset - pre;
    this.t0 = this.context.currentTime + lead + this.countdown;
    this.sourceWhen = this.t0 - pre / this.rate;
    this.src = this.context.createBufferSource(); this.src.buffer = this.buffer;
    this.src.playbackRate.value = this.rate;
    this.gain = this.context.createGain();
    this.gain.gain.setValueAtTime(this.countdown ? 0.25 : 1, this.context.currentTime);
    if (this.countdown) {
      this.gain.gain.setValueAtTime(0.25, this.t0 - 0.02);
      this.gain.gain.linearRampToValueAtTime(1, this.t0);
    }
    this.src.connect(this.gain); this.gain.connect(this.context.destination);
    this.src.onended = () => {
      this.endTimer = setTimeout(() => this.finish(), this.latency * 1000);
    };
    this.src.start(this.sourceWhen, this.sourceOffset, pre + this.duration);
    const tick = () => {
      if (this.closed) return;
      const left = this.t0 + this.latency - this.context.currentTime;
      if (left > 0) this.onCount(Math.min(3, Math.max(1, Math.ceil(left))));
      else {
        if (!this.running) { this.running = true; this.onRun(); }
        if (this.closed) return;
        this.onTick(this.elapsed());
      }
      this.raf = requestAnimationFrame(tick);
    };
    tick(); return true;
  }
  elapsed() {
    return Math.max(0, Math.min(this.duration,
      (this.context.currentTime - this.t0 - this.latency) * this.rate));
  }
  finish() {
    if (this.closed) return;
    this.stop(); this.onEnd();
  }
  stop() {
    this.closed = true; cancelAnimationFrame(this.raf); clearTimeout(this.endTimer);
    if (this.src) {
      this.src.onended = null;
      try { this.src.stop(); } catch (_) {}
      this.src.disconnect();
    }
    if (this.gain) this.gain.disconnect();
  }
};
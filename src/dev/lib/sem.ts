// semaphores but able to assign different work functions
export class JobManager {
  constructor(
    workers: (job: J) => Promise<R>,
    options?: {
      verbose?: boolean,
      cache?: boolean,
    }
  ) {
    this.workers = workers;
    this.options = options || {};
  }

  async run(jobs: J[]): Promise<R[]> {
    // const unfinished: { job: J[], index: number }[] = jobs.map((job, index) => ({ job, index } ));
    const unfinished: { job: J[], index: number }[] = [];
    const results: { result: R, index: number }[] = [];

    const hash = Bun.hash(jobs).toString(16);
    const cache = Bun.file(`.cache/${hash}.json`);
    if (this.options.cache && await cache.exists()) {
      const { results: cachedResults } = await cache.json();
      results.push(...cachedResults);
      unfinished.push(...jobs
        .map((job, index) => ({ job, index }))
        .filter(({ index }) => !cachedResults.some(({ index: i_finished }) => index === i_finished))
      );
      if (this.options.verbose)
        console.log(`Cache found, picking up from there (${results.length}/${jobs.length})`);
    }
    else
      unfinished.push(...jobs.map((job, index) => ({ job, index })));

    // runners
    await Promise.all(
      this.workers.map(async (worker) => {
        while (unfinished.length > 0) {
          const { job, index } = unfinished.shift()!;
          try {
            const result = await worker(job);
            if (this.options.verbose)
              console.log(`${results.length + 1}/${jobs.length} done`);
            results.push({ result, index });
          }
          catch (error) {
            if (this.options.verbose)
              console.error(`Job ${index} failed: ${error}`);
            unfinished.push({ job, index });
          }
          if (this.options.cache)
            await Bun.write(
              cache,
              JSON.stringify({ results })
            );
        }
      }
    ));

    return results
      .sort((a, b) => a.index - b.index)
      .map(({ result }) => result);
  }
}

import type { PropsWithChildren } from 'react';

export function Panel({
  title,
  children,
}: PropsWithChildren<{ title: string }>) {
  return (
    <section className="panel p-6 sm:p-8">
      <h2 className="mb-6 font-display text-3xl">{title}</h2>
      {children}
    </section>
  );
}

export default function NextError({ statusCode }: { statusCode: number }) {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-red-700">
        Something went wrong ({statusCode || "unknown"}).
      </div>
    </div>
  );
}

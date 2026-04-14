interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
}

export default function ProgressBar({ value, max = 100, label }: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-sm mb-1">
          <span className="text-dark-300">{label}</span>
          <span className="text-white font-medium">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="w-full h-2 bg-dark-900 rounded-full overflow-hidden">
        <div
          className="h-full bg-accent-600 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

import React from 'react';

const MotorGauge = ({ label, value, color = '#6366f1', min = 0, max = 360 }) => {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const percentage = (value - min) / (max - min);
    const strokeDashoffset = circumference - (percentage * circumference);

    return (
        <div className="card glass glass-hover pulse-on-change">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-dim">{label}</h3>
                <span className="mono text-gradient font-bold">{value.toFixed(2)}°</span>
            </div>

            <div className="flex justify-center relative">
                <svg viewBox="0 0 100 100" className="w-48 h-48 transform -rotate-90">
                    {/* Background Track */}
                    <circle
                        cx="50"
                        cy="50"
                        r={radius}
                        fill="none"
                        stroke="rgba(255, 255, 255, 0.05)"
                        strokeWidth="8"
                    />
                    {/* Progress Bar */}
                    <circle
                        cx="50"
                        cy="50"
                        r={radius}
                        fill="none"
                        stroke={color}
                        strokeWidth="8"
                        strokeLinecap="round"
                        style={{
                            transition: 'stroke-dashoffset 0.5s ease-out',
                            strokeDasharray: circumference,
                            strokeDashoffset: strokeDashoffset,
                            filter: `drop-shadow(0 0 8px ${color}80)`
                        }}
                    />
                </svg>

                {/* Center Label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-xs text-muted uppercase tracking-widest">Orbit</span>
                    <span className="stat-value text-3xl font-bold">{Math.floor(percentage * 100)}%</span>
                </div>
            </div>

            <div className="flex gap-2 mt-6">
                <button className="btn btn-ghost flex-1 text-xs">MIN</button>
                <button className="btn btn-ghost flex-1 text-xs">MAX</button>
            </div>
        </div>
    );
};

export default MotorGauge;

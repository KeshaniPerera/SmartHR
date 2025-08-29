import { useEffect, useRef, useState } from "react";

/**
 * Polished Attendance scanner page (pure JS)
 * - Opens webcam
 * - Lets user pick a camera
 * - One-click Scan or Auto-scan (every few seconds)
 * - Sends frame to Django: POST `${API_BASE}/api/attendance/scan`
 * - Shows friendly status + last result (IN/OUT/Invalid Entry)
 *
 * TailwindCSS required (basic styles used)
 */
export default function AttendanceScan() {
  const API_BASE = import.meta.env.VITE_API_BASE || ""; // e.g. "http://localhost:8000"

  // refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const currentStream = useRef(null);

  // state
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [autoScan, setAutoScan] = useState(false);
  const [autoScanMs, setAutoScanMs] = useState(3500);
  const [status, setStatus] = useState("Ready");
  const [last, setLast] = useState(null);

  // permissions + enumerate cameras
  useEffect(() => {
    (async () => {
      try {
        // request a temp stream to unlock enumerateDevices labels on some browsers
        const tmp = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        tmp.getTracks().forEach(t => t.stop());
      } catch (e) {
        // user may deny, we'll still try enumerateDevices
      }
      const all = await navigator.mediaDevices.enumerateDevices();
      const cams = all.filter(d => d.kind === "videoinput");
      setDevices(cams);
      if (cams.length && !deviceId) setDeviceId(cams[0].deviceId);
    })();
  }, []);

  const startCamera = async () => {
    if (!deviceId) return;
    setIsStarting(true);
    stopCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: { exact: deviceId },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      currentStream.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsRunning(true);
      setStatus("Camera ready");
    } catch (err) {
      console.error(err);
      setStatus("Camera error: " + (err && err.message ? err.message : "unknown"));
      setIsRunning(false);
    } finally {
      setIsStarting(false);
    }
  };

  const stopCamera = () => {
    if (currentStream.current) {
      currentStream.current.getTracks().forEach(t => t.stop());
      currentStream.current = null;
    }
    setIsRunning(false);
  };

  useEffect(() => {
    // auto start camera once we know a device
    if (deviceId) {
      startCamera();
    }
    return () => stopCamera();
  }, [deviceId]);

  const captureDataURL = () => {
    const v = videoRef.current;
    const c = canvasRef.current;
    if (!v || !c || !v.videoWidth || !v.videoHeight) return null;

    // resize for payload efficiency (max side ~720)
    const maxSide = 720;
    var w = v.videoWidth, h = v.videoHeight;
    const scale = Math.min(1, maxSide / Math.max(w, h));
    const W = Math.max(1, Math.round(w * scale));
    const H = Math.max(1, Math.round(h * scale));

    c.width = W; c.height = H;
    const ctx = c.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(v, 0, 0, W, H);
    return c.toDataURL("image/jpeg", 0.9);
  };

  const scanOnce = async () => {
    if (!isRunning) {
      setStatus("Camera not running");
      return;
    }
    const dataUrl = captureDataURL();
    if (!dataUrl) {
      setStatus("Capture failed");
      return;
    }
    setStatus("Scanning...");
    try {
      const res = await fetch(`${API_BASE}/api/attendance/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageBase64: dataUrl }),
      });
      const j = await res.json();
      if (!j.ok) {
        setStatus("Invalid Entry");
        setLast(j);
        flashBorder("ring-red-500");
      } else {
        const label = j.type && j.type.indexOf("OUT") === 0 ? "Recorded OUT" : "Recorded IN";
        setStatus(label);
        setLast(j);
        flashBorder(j.type && j.type.indexOf("OUT") === 0 ? "ring-amber-500" : "ring-emerald-500");
      }
    } catch (e) {
      console.error(e);
      setStatus("Server error");
    }
  };

  const flashBorder = (ringClass) => {
    const wrap = document.getElementById("scan-wrap");
    if (!wrap) return;
    wrap.classList.remove("ring-red-500", "ring-emerald-500", "ring-amber-500");
    wrap.classList.add(ringClass);
    wrap.classList.add("ring-4");
    setTimeout(() => {
      wrap.classList.remove("ring-4", ringClass);
    }, 700);
  };

  // auto-scan timer
  useEffect(() => {
    if (!autoScan) {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }
    intervalRef.current = window.setInterval(() => {
      scanOnce();
    }, autoScanMs);
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoScan, autoScanMs]);

  const ConfidenceBadge = ({ value }) => {
    if (value == null) return null;
    const pct = Math.round(value * 100);
    const tone = pct >= 60 ? "bg-emerald-600" : pct >= 45 ? "bg-amber-600" : "bg-rose-600";
    return (
      <span className={`text-white text-xs px-2 py-1 rounded ${tone}`}>{pct}%</span>
    );
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Attendance</h1>

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm">Camera</label>
        <select
          className="border rounded px-2 py-1"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
        >
          {devices.map((d, i) => (
            <option key={d.deviceId || i} value={d.deviceId}>
              {d.label || `Camera ${i + 1}`}
            </option>
          ))}
        </select>

        <button
          onClick={startCamera}
          disabled={isStarting}
          className="px-3 py-1 rounded bg-slate-800 text-white disabled:opacity-50"
        >
          {isStarting ? "Starting..." : "Restart Camera"}
        </button>

        <div className="flex items-center gap-2 ml-auto">
          <label className="text-sm flex items-center gap-2">
            <input type="checkbox" checked={autoScan} onChange={e => setAutoScan(e.target.checked)} />
            Auto-scan
          </label>
          <select
            className="border rounded px-2 py-1"
            value={autoScanMs}
            onChange={(e) => setAutoScanMs(parseInt(e.target.value, 10))}
          >
            <option value={2500}>Every 2.5s</option>
            <option value={3500}>Every 3.5s</option>
            <option value={5000}>Every 5s</option>
          </select>
        </div>
      </div>

      <div id="scan-wrap" className="relative inline-block rounded-2xl overflow-hidden shadow-md">
        <video ref={videoRef} autoPlay playsInline className="w-full max-w-2xl aspect-video bg-black" />
        {/* aesthetic overlay */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/10 via-transparent to-black/10" />
      </div>
      <canvas ref={canvasRef} className="hidden" />

      <div className="flex gap-3">
        <button
          onClick={scanOnce}
          disabled={!isRunning}
          className="px-4 py-2 rounded-2xl bg-black text-white disabled:bg-gray-400"
        >
          Scan Now
        </button>
        <span className="text-sm self-center">Status: <b>{status}</b></span>
      </div>

      {last && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-3 rounded-xl bg-slate-50 border">
            <div className="text-sm text-slate-500 mb-1">Last result</div>
            {last.ok ? (
              <div className="flex items-center gap-3">
                <div className={`px-2 py-1 rounded text-white text-xs ${
                  last.type && last.type.indexOf("OUT") === 0 ? "bg-amber-600" : "bg-emerald-600"
                }`}>{last.type}</div>
                <div className="text-sm">Employee: <b>{last.employeeCode}</b></div>
                <ConfidenceBadge value={last.confidence} />
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="px-2 py-1 rounded text-white text-xs bg-rose-600">Invalid</div>
                <div className="text-sm">Reason: {last.reason || "unknown"}</div>
                {last.confidence != null && <ConfidenceBadge value={last.confidence} />}
              </div>
            )}
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border text-xs">
            <div className="text-slate-500 mb-1">Debug payload</div>
            <pre className="max-h-48 overflow-auto">{JSON.stringify(last, null, 2)}</pre>
          </div>
        </div>
      )}

      <div className="text-xs text-slate-500">
        Tip: if the camera fails to start, switch devices or allow camera permissions in your browser.
      </div>
    </div>
  );
}

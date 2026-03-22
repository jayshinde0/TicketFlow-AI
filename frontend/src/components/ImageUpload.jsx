/**
 * components/ImageUpload.jsx — Drag-and-drop image upload with preview.
 * Client-side validation for file type, size, and count.
 */
import React, { useRef, useState, useCallback } from "react";
import { X, Upload, Image as ImageIcon } from "lucide-react";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];
const ALLOWED_EXT = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
const MAX_FILES = 3;

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ImageUpload({ files, setFiles }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [errors, setErrors] = useState([]);

  const validate = useCallback((fileList) => {
    const errs = [];
    const accepted = [];

    for (const f of fileList) {
      const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
      if (!ALLOWED_TYPES.includes(f.type) && !ALLOWED_EXT.includes(ext)) {
        errs.push(`"${f.name}" — unsupported format. Use JPG, PNG, WebP, or GIF.`);
        continue;
      }
      if (f.size > MAX_SIZE_BYTES) {
        errs.push(`"${f.name}" — too large (${formatSize(f.size)}). Max 5MB.`);
        continue;
      }
      accepted.push(f);
    }

    const totalAfter = files.length + accepted.length;
    if (totalAfter > MAX_FILES) {
      const canAdd = MAX_FILES - files.length;
      errs.push(`Only ${canAdd} slot(s) remaining. ${accepted.length - canAdd} file(s) skipped.`);
      accepted.splice(canAdd);
    }

    setErrors(errs);
    if (accepted.length > 0) {
      setFiles((prev) => [...prev, ...accepted]);
    }
  }, [files, setFiles]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) validate([...e.dataTransfer.files]);
  };

  const handleFileInput = (e) => {
    if (e.target.files.length) validate([...e.target.files]);
    e.target.value = "";
  };

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
    setErrors([]);
  };

  return (
    <div>
      <label className="label">Attach Screenshots (optional)</label>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => files.length < MAX_FILES && inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragOver ? "#6366f1" : "#374151"}`,
          borderRadius: "12px",
          padding: "1.25rem",
          textAlign: "center",
          cursor: files.length < MAX_FILES ? "pointer" : "not-allowed",
          background: dragOver ? "rgba(99,102,241,0.05)" : "transparent",
          transition: "all 0.2s",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_EXT.join(",")}
          multiple
          onChange={handleFileInput}
          style={{ display: "none" }}
        />
        <Upload size={24} style={{ margin: "0 auto 0.5rem", color: "#9ca3af" }} />
        <p style={{ color: "#9ca3af", fontSize: "0.85rem" }}>
          {files.length < MAX_FILES
            ? "Click or drag images here"
            : "Maximum images reached"}
        </p>
        <p style={{ color: "#6b7280", fontSize: "0.75rem", marginTop: "0.25rem" }}>
          {files.length} of {MAX_FILES} slots used · JPG, PNG, WebP, GIF · Max 5MB each
        </p>
      </div>

      {/* Errors */}
      {errors.length > 0 && (
        <div style={{ marginTop: "0.5rem" }}>
          {errors.map((err, i) => (
            <p key={i} style={{ color: "#ef4444", fontSize: "0.8rem", margin: "0.15rem 0" }}>⚠ {err}</p>
          ))}
        </div>
      )}

      {/* Previews */}
      {files.length > 0 && (
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          {files.map((f, i) => (
            <div key={i} style={{
              position: "relative",
              width: "100px",
              borderRadius: "10px",
              overflow: "hidden",
              border: "1px solid #374151",
              background: "#1e293b",
            }}>
              <img
                src={URL.createObjectURL(f)}
                alt={f.name}
                style={{ width: "100%", height: "80px", objectFit: "cover" }}
              />
              <div style={{ padding: "0.25rem 0.35rem" }}>
                <p style={{
                  fontSize: "0.65rem", color: "#e2e8f0", whiteSpace: "nowrap",
                  overflow: "hidden", textOverflow: "ellipsis",
                }}>{f.name}</p>
                <p style={{ fontSize: "0.6rem", color: "#9ca3af" }}>{formatSize(f.size)}</p>
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                style={{
                  position: "absolute", top: "4px", right: "4px",
                  width: "20px", height: "20px", borderRadius: "50%",
                  background: "rgba(0,0,0,0.7)", border: "none",
                  color: "#fff", cursor: "pointer", display: "flex",
                  alignItems: "center", justifyContent: "center",
                }}
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (base64: string | null) => void;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageSelected }) => {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setErrorMsg('Invalid format. Only JPG, PNG, and WebP medical images are accepted.');
      return;
    }

    // Validate size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 5 MB limit.');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      setImagePreview(base64);
      onImageSelected(base64);
    };
    reader.readAsDataURL(file);
  };

  const handleRemove = () => {
    setImagePreview(null);
    setErrorMsg(null);
    onImageSelected(null);
  };

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <ImageIcon className="w-5 h-5 text-medic-teal" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Emergency Visual Upload</h3>
        </div>
        <span className="text-[11px] text-slate-400">Max 5MB • JPG, PNG, WebP</span>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-emergency-950/40 border border-emergency-500/40 text-emergency-400 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {!imagePreview ? (
        <label className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-navy-700 hover:border-medic-teal rounded-xl bg-navy-950/60 cursor-pointer transition-colors group">
          <UploadCloud className="w-10 h-10 text-slate-400 group-hover:text-medic-teal transition-colors mb-2" />
          <span className="text-xs font-semibold text-slate-200">Click to upload emergency image or drag & drop</span>
          <span className="text-[11px] text-slate-500 mt-1">E.g., external wound, rash, burn area, medication bottle</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
      ) : (
        <div className="relative rounded-xl overflow-hidden border border-navy-700 bg-navy-950">
          <img src={imagePreview} alt="Emergency finding" className="w-full max-h-64 object-contain mx-auto" />
          <button
            type="button"
            onClick={handleRemove}
            className="absolute top-2 right-2 p-1.5 rounded-full bg-black/70 hover:bg-emergency-600 text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="p-3 bg-navy-950/90 border-t border-navy-800 flex items-center justify-between text-xs">
            <span className="text-emerald-400 flex items-center gap-1 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Image validated & ready for clinical inspection
            </span>
          </div>
        </div>
      )}

      {/* Medical Safety Disclaimer for Vision Input */}
      <div className="mt-4 p-3 rounded-lg bg-navy-950 border border-navy-800 text-[11px] text-slate-400 leading-relaxed">
        <span className="font-bold text-slate-300">Safety Rule: </span>
        The AI vision pipeline extracts visible physical findings only (e.g. erythema, bleeding, swelling).
        It never renders a definitive diagnosis solely from photographic evidence.
      </div>
    </div>
  );
};

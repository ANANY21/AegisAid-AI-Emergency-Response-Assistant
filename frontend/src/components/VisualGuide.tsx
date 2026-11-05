import React from 'react';
import { Heart, Activity, ShieldAlert, Waves, Droplet, UserCheck } from 'lucide-react';

interface VisualGuideProps {
  guideKey?: 'cpr' | 'heimlich' | 'pressure_bandage' | 'burns_water' | 'recovery_position' | null;
}

export const VisualGuide: React.FC<VisualGuideProps> = ({ guideKey }) => {
  if (!guideKey) return null;

  switch (guideKey) {
    case 'cpr':
      return (
        <div className="bg-navy-900 border border-emergency-500/40 rounded-xl p-4 my-3 text-slate-200">
          <div className="flex items-center gap-2 mb-2 text-emergency-500 font-bold text-sm">
            <Heart className="w-4 h-4 animate-ping text-emergency-500" />
            <span>CLINICAL PROTOCOL: ADULT HANDS-ONLY CPR (AHA/ERC GUIDELINE)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-emergency-600/20 text-emergency-400 flex items-center justify-center font-bold text-lg mb-2">1</div>
              <span className="font-semibold text-white">Center of Chest</span>
              <span className="text-slate-400 mt-1">Interlock both hands, heel in center of breastbone between nipples.</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-emergency-600/20 text-emergency-400 flex items-center justify-center font-bold text-lg mb-2">2</div>
              <span className="font-semibold text-white">100 - 120 BPM</span>
              <span className="text-slate-400 mt-1">Push hard and fast to rhythm of "Stayin' Alive". Lock elbows.</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 flex flex-col items-center text-center">
              <div className="w-10 h-10 rounded-full bg-emergency-600/20 text-emergency-400 flex items-center justify-center font-bold text-lg mb-2">3</div>
              <span className="font-semibold text-white">2 Inches (5 cm)</span>
              <span className="text-slate-400 mt-1">Compress 2 to 2.4 inches. Allow full chest recoil between compressions.</span>
            </div>
          </div>
        </div>
      );

    case 'heimlich':
      return (
        <div className="bg-navy-900 border border-amber-500/40 rounded-xl p-4 my-3 text-slate-200">
          <div className="flex items-center gap-2 mb-2 text-amber-400 font-bold text-sm">
            <Activity className="w-4 h-4 text-amber-400" />
            <span>AIRWAY DISLODGEMENT: 5 BACK BLOWS & 5 ABDOMINAL THRUSTS</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800">
              <span className="font-bold text-amber-400 block mb-1">Step A: 5 Firm Back Blows</span>
              <p className="text-slate-300">Lean casualty forward supporting chest with one arm. Strike sharply between shoulder blades with the heel of your hand.</p>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800">
              <span className="font-bold text-amber-400 block mb-1">Step B: 5 Abdominal Thrusts</span>
              <p className="text-slate-300">Stand behind casualty. Thumb-side of fist placed just above navel. Grasp with other hand and pull sharply inward and upward.</p>
            </div>
          </div>
        </div>
      );

    case 'pressure_bandage':
      return (
        <div className="bg-navy-900 border border-emergency-500/40 rounded-xl p-4 my-3 text-slate-200">
          <div className="flex items-center gap-2 mb-2 text-emergency-400 font-bold text-sm">
            <ShieldAlert className="w-4 h-4 text-emergency-400" />
            <span>HEMORRHAGE CONTROL: STOP THE BLEED GUIDELINE</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800">
              <span className="font-bold text-white block mb-1">Direct Uninterrupted Pressure</span>
              <p className="text-slate-300">Place clean cloth/gauze directly over bleeding site. Lean full body weight onto wound. Never remove soaked dressings; stack more on top.</p>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800">
              <span className="font-bold text-white block mb-1">Limb Tourniquet (If Catastrophic)</span>
              <p className="text-slate-300">Place 2-3 inches above wound on arm/leg (never over joint). Twist windlass rod until bright red bleeding ceases. Note exact application time.</p>
            </div>
          </div>
        </div>
      );

    case 'burns_water':
      return (
        <div className="bg-navy-900 border border-medic-teal/40 rounded-xl p-4 my-3 text-slate-200">
          <div className="flex items-center gap-2 mb-2 text-medic-teal font-bold text-sm">
            <Waves className="w-4 h-4 text-medic-teal" />
            <span>THERMAL INJURY: THE 20-MINUTE WATER RULE (WHO PROTOCOL)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 text-center">
              <Droplet className="w-5 h-5 text-medic-teal mx-auto mb-1" />
              <span className="font-bold text-white block">20 Minutes Running Water</span>
              <span className="text-slate-400">Cool immediately under cool tap water (15-20°C). Never use ice.</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 text-center">
              <span className="font-bold text-white block mb-1">Remove Constrictions</span>
              <span className="text-slate-400">Gently remove rings, watches, and tight clothes before swelling develops.</span>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-navy-800 text-center">
              <span className="font-bold text-white block mb-1">Loose Cling Wrap</span>
              <span className="text-slate-400">Cover loosely with plastic wrap layers to protect exposed nerve endings.</span>
            </div>
          </div>
        </div>
      );

    case 'recovery_position':
      return (
        <div className="bg-navy-900 border border-blue-500/40 rounded-xl p-4 my-3 text-slate-200">
          <div className="flex items-center gap-2 mb-2 text-blue-400 font-bold text-sm">
            <UserCheck className="w-4 h-4 text-blue-400" />
            <span>AIRWAY PROTECTION: LATERAL RECOVERY POSITION</span>
          </div>
          <p className="text-xs text-slate-300">
            For unresponsive breathing casualties: Kneel beside casualty. Place nearest arm at a right angle.
            Bring far arm across chest. Bend far leg at knee and gently roll them toward you onto their side.
            Tilt head back gently to ensure airway remains open and saliva or vomit drains freely.
          </p>
        </div>
      );

    default:
      return null;
  }
};

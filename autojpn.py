import os
import wave
import math
import array
from datetime import datetime

# Define paths
consonant_path = r"this\is\a\PATH"
vowel_path = r"this\is\a\PATH"
output_path = r"this\is\a\PATH"

# Ensure output directory exists
os.makedirs(output_path, exist_ok=True)

# Vowel list
vowels = ['a', 'e', 'u', 'i', 'o', 'n']

# Recording table
recording_table = [
    "a_i_u_e_o_a",
    "a_u_o_i_e_a",
    "a_e_i_o_u_a",
    "a_o_e_u_i_a",
    "a_i_u_e_o_n",
    "ka_ki_ku_ke_ko_kya_kyu_kye_kyo",
    "ga_gi_gu_ge_go_gya_gyu_gye_gyo",
    "nga_ngi_ngu_nge_ngo_ngya_ngyu_ngye_ngyo",
    "sa_si_su_se_so",
    "za_zi_zu_ze_zo",
    "sha_shi_shu_she_sho",
    "ja_ji_ju_je_jo",
    "tsa_tsi_tsu_tse_tso",
    "dza_dzi_dzu_dze_dzo",
    "cha_chi_chu_che_cho",
    "dja_dji_dju_dje_djo",
    "ta_ti_tu_te_to_tya_tyu_tye_tyo",
    "da_di_du_de_do_dya_dyu_dye_dyo",
    "pa_pi_pu_pe_po_pya_pyu_pye_pyo",
    "ba_bi_bu_be_bo_bya_byu_bye_byo",
    "fa_fi_fu_fe_fo_fya_fyu_fye_fyo",
    "ma_mi_mu_me_mo_mya_myu_mye_myo",
    "ra_ri_ru_re_ro_rya_ryu_rye_ryo",
    "ya_yi_yu_ye_yo",
    "wa_wi_wu_we_wo",
    "va_vi_vu_ve_vo",
    "ha_hi_hu_he_ho",
    "hya_hyi_hyu_hye_hyo",
    "na_ni_nu_ne_no",
    "nya_nyi_nyu_nye_nyo",
    "jya_jyu_jye_jyo",
    "sya_syi_syu_sye_syo",
    "kwa_kwi_kwu_kwe_kwo_ka",
    "gwa_gwi_gwu_gwe_gwo_ga",
    "rwa_rwi_rwu_rwe_rwo_ra"
]

def read_wav(file_path):
    """Read WAV file, return audio data and parameters"""
    try:
        with wave.open(file_path, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
            # Convert byte data to array
            if params.sampwidth == 2:
                audio_data = array.array('h', frames)
            else:
                # If not 16-bit, need to convert
                raise ValueError("Only 16-bit audio is supported")
            return audio_data, params
    except Exception as e:
        raise Exception(f"Cannot read file {file_path}: {str(e)}")

def write_wav(file_path, audio_data, params):
    """Write audio data to WAV file"""
    try:
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setparams(params)
            # Convert array to byte data
            wav_file.writeframes(audio_data.tobytes())
    except Exception as e:
        raise Exception(f"Cannot write file {file_path}: {str(e)}")

def crossfade(audio1, audio2, fade_length):
    """Apply crossfade between two audio segments"""
    result = array.array('h')
    
    # First audio segment (minus fade length)
    for i in range(len(audio1) - fade_length):
        result.append(audio1[i])
    
    # Crossfade section
    for i in range(fade_length):
        if i < len(audio1) - fade_length:
            continue  # Already processed
        
        idx1 = len(audio1) - fade_length + i
        idx2 = i
        
        if idx1 < len(audio1) and idx2 < len(audio2):
            # Calculate fade factors
            factor1 = 1.0 - (i / fade_length)
            factor2 = i / fade_length
            
            # Apply crossfade
            sample = int(audio1[idx1] * factor1 + audio2[idx2] * factor2)
            result.append(sample)
    
    # Remaining part of second audio
    for i in range(fade_length, len(audio2)):
        result.append(audio2[i])
    
    return result

def concatenate_audio(consonant_data, vowel_data, params):
    """Concatenate consonant and vowel audio"""
    # Calculate 55% position of consonant
    consonant_cut_pos = int(len(consonant_data) * 0.55)
    
    # Extract first 55% of consonant
    consonant_part = consonant_data[:consonant_cut_pos]
    
    # Calculate fade length (10% of shorter audio)
    fade_length = min(int(len(consonant_data) * 0.1), int(len(vowel_data) * 0.1))
    fade_length = max(10, fade_length)  # Ensure at least 10 samples
    
    # Crossfade between remaining consonant and vowel
    consonant_remainder = consonant_data[consonant_cut_pos:]
    faded_part = crossfade(consonant_remainder, vowel_data, fade_length)
    
    # Concatenate audio
    result = array.array('h')
    result.extend(consonant_part)
    result.extend(faded_part)
    
    return result

def process_syllable(syllable, error_report):
    """Process a single syllable"""
    # Check if output file already exists
    output_file = os.path.join(output_path, f"{syllable}.wav")
    if os.path.exists(output_file):
        print(f"Skipping existing syllable: {syllable}")
        return True
    
    # Check if it's a pure vowel
    if syllable in vowels:
        # Directly copy vowel file
        vowel_file = os.path.join(vowel_path, f"{syllable}.wav")
        if os.path.exists(vowel_file):
            try:
                vowel_data, params = read_wav(vowel_file)
                write_wav(output_file, vowel_data, params)
                print(f"Copied vowel: {syllable}")
                return True
            except Exception as e:
                error_report.append(f"Error processing vowel {syllable}: {str(e)}")
                return False
        else:
            error_msg = f"Vowel file not found: {vowel_file}"
            error_report.append(error_msg)
            print(f"Warning: {error_msg}")
            return False
    
    # Separate consonant and vowel parts
    consonant_part = None
    vowel_part = None
    
    # Try different consonant lengths (from long to short)
    for i in range(min(4, len(syllable)), 0, -1):
        consonant_candidate = syllable[:i]
        vowel_candidate = syllable[i:]
        
        if vowel_candidate in vowels:
            consonant_part = consonant_candidate
            vowel_part = vowel_candidate
            break
    
    if consonant_part is None or vowel_part is None:
        error_msg = f"Cannot parse syllable: {syllable}"
        error_report.append(error_msg)
        print(f"Warning: {error_msg}")
        return False
    
    # Build consonant filename
    consonant_file = os.path.join(consonant_path, f"{consonant_part}-.wav")
    vowel_file = os.path.join(vowel_path, f"{vowel_part}.wav")
    
    # Check if files exist
    if not os.path.exists(consonant_file):
        error_msg = f"Consonant file not found: {consonant_file}"
        error_report.append(error_msg)
        print(f"Warning: {error_msg}")
        return False
    
    if not os.path.exists(vowel_file):
        error_msg = f"Vowel file not found: {vowel_file}"
        error_report.append(error_msg)
        print(f"Warning: {error_msg}")
        return False
    
    try:
        # Read audio files
        consonant_data, consonant_params = read_wav(consonant_file)
        vowel_data, vowel_params = read_wav(vowel_file)
        
        # Ensure parameters match
        if consonant_params.sampwidth != 2 or vowel_params.sampwidth != 2:
            error_msg = f"Audio is not 16-bit format: {syllable}"
            error_report.append(error_msg)
            print(f"Warning: {error_msg}")
            return False
        
        if consonant_params.nchannels != 1 or vowel_params.nchannels != 1:
            error_msg = f"Audio is not mono: {syllable}"
            error_report.append(error_msg)
            print(f"Warning: {error_msg}")
            return False
        
        if consonant_params.framerate != 44100 or vowel_params.framerate != 44100:
            error_msg = f"Audio sample rate is not 44100Hz: {syllable}"
            error_report.append(error_msg)
            print(f"Warning: {error_msg}")
            return False
        
        # Concatenate audio
        combined_audio = concatenate_audio(consonant_data, vowel_data, consonant_params)
        
        # Write output file
        write_wav(output_file, combined_audio, consonant_params)
        print(f"Processed: {syllable}")
        return True
    except Exception as e:
        error_msg = f"Error processing syllable {syllable}: {str(e)}"
        error_report.append(error_msg)
        print(f"Error: {error_msg}")
        return False

def generate_error_report(error_report):
    """Generate error report"""
    if not error_report:
        return
    
    # Create error report file
    report_file = os.path.join(output_path, f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Audio Concatenation Error Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total errors: {len(error_report)}\n\n")
        
        for i, error in enumerate(error_report, 1):
            f.write(f"{i}. {error}\n")
    
    print(f"\nError report generated: {report_file}")

def main():
    """Main function"""
    print("Starting audio concatenation...")
    
    # Initialize error report
    error_report = []
    processed_count = 0
    error_count = 0
    
    # Process all syllables in recording table
    for line in recording_table:
        syllables = line.split('_')
        for syllable in syllables:
            if process_syllable(syllable, error_report):
                processed_count += 1
            else:
                error_count += 1
    
    # Generate error report
    generate_error_report(error_report)
    
    print(f"\nProcessing complete! Successful: {processed_count}, Failed: {error_count}")

if __name__ == "__main__":
    main()
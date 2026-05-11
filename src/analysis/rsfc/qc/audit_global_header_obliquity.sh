
#!/bin/bash
# FILENAME: audit_all_participants_headers.sh
# A diagnostic Quality Control (QC) tool. It doesn't modify data. 

# Complete Subject List (Normals + 29)
subjects=( 5 6 9 14 15 17 18 22 24 25 26 27 28 29 35 38 39 40 41 42 43 46 47 48 50 51 53 54 )
PARTICIPANTS_ROOT="/[put participants root here]"

LOG_FILE="${PARTICIPANTS_ROOT}/logs/global_obliquity_audit.txt"
mkdir -p "${PARTICIPANTS_ROOT}/logs"

echo "========================================================"
echo "GLOBAL HEADER AUDIT (CHECKING FOR OBLIQUITY)"
echo "Target: All subjects, all sessions."
echo "Save path: $LOG_FILE"
echo "========================================================"

echo "Subject,File,Oblique_Status" > "$LOG_FILE"
printf "%-12s | %-12s | %-10s | %s\n" "SUBJECT" "SESSION" "STATUS" "RESULT"

count_clean=0
count_oblique=0
count_missing=0

suffixes=("" "_session-1" "_session-2" "_session-3")

for id in "${subjects[@]}"; do
    subj="subject-${id}"
    searchlight_dir="${PARTICIPANTS_ROOT}/${subj}/decoding_dice2decnef/searchlight_hitrate"
    
    if [ ! -d "$searchlight_dir" ]; then
        echo "   [SKIP] $subj (No searchlight folder)"
        continue
    fi
    
    cd "$searchlight_dir" || continue

    for s_id in "${suffixes[@]}"; do
        if [ -z "$s_id" ]; then sess_name="Main"; else sess_name="${s_id}"; fi
        
        file="dice2decnef_searchlight_results_logistic_probs_radius_4${s_id}.nii.gz"
        
        if [ -f "$file" ]; then
            is_obl=$(3dinfo -is_oblique "$file" 2>/dev/null)
            
            if [ "$is_obl" == "1" ]; then
                printf "%-12s | %-12s | \e[31mWARNING\e[0m    | Header is OBLIQUE (Tilted)\n" "$subj" "$sess_name"
                echo "$subj,$sess_name,OBLIQUE" >> "$LOG_FILE"
                ((count_oblique++))
            else
                printf "%-12s | %-12s | \e[32mOK\e[0m         | Header is Straight\n" "$subj" "$sess_name"
                echo "$subj,$sess_name,CLEAN" >> "$LOG_FILE"
                ((count_clean++))
            fi
        else
            ((count_missing++))
        fi
    done
done

echo "========================================================"
echo "AUDIT COMPLETE"
echo "Clean Files:   $count_clean"
echo "Oblique Files: $count_oblique (Check these!)"
echo "========================================================"

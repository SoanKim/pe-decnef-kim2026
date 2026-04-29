module load afni/latest
module load python/python3

## credit: David, Cesar, Soan, and major support by Paul Taylor (AFNI Mailing List)
# https://discuss.afni.nimh.nih.gov/t/afni-coregistration-of-a-searchlight-decoding-map-from-native-to-standard/8748

# subject
sub=$(basename "${PWD%/*}")

# decoder dir
decoder_dir=/[put your decoder directory]/$sub
# induction dir
induction_dir=/[put your decoder directory]/$sub
# dice dir
dice_dir=$induction_dir/decoding_dice2decnef/searchlight_hitrate

# T1 dir
T1=$decoder_dir/raw/T1/output_brain

# deobliqued reference (example_func) dir
sbref=$decoder_dir/preprocessed/example_func/example_func_deoblique_brain

#this is path to afni mni template in bcbl cluster
MNItemplate=/opt/afni/linux_openmp_64/MNI152_2009_template.nii.gz
#dxyz=$(3dinfo -adi ${sbref}.nii)

##################### NO USE ####################
#echo ---------------------------------------------------------
#echo "Coregistration of anatomical image to functional image" 
#echo ---------------------------------------------------------
# ================================= align ==================================
#align_epi_anat.py -anat2epi -giant_move -anat ${T1}_DEOB.nii -suffix _al_epi \
#    -epi ${sbref}.nii -epi_base 0 \
#    -anat_has_skull no -epi_strip None -volreg off -tshift off -overwrite
##################### NO USE ####################

# Refer to afni mailing list here https://discuss.afni.nimh.nih.gov/t/error-during-afni-coregistration-of-a-reference-image/8774/2

echo ---------------------------------------------------------
echo "Deobliquing T1" 
echo ---------------------------------------------------------
adjunct_deob_around_origin \
    -input ${T1}.nii \
    -prefix ${T1}_DEOB.nii

echo ---------------------------------------------------------
echo "Cost Function-Based Alignment" 
echo ---------------------------------------------------------

align_epi_anat.py \
    -anat2epi -giant_move \
    -anat ${T1}_DEOB.nii \
    -suffix _al_epi2 \
    -epi ${sbref}.nii \
    -epi_base 0   \
    -anat_has_skull no \
    -epi_strip None -volreg off -tshift off -overwrite

echo ---------------------------------------------------------
echo "Local Unifizing: Adjusting the Brightness in the EPI" 
echo ---------------------------------------------------------
# [0] is a sub-brick(s) selector, taking the first 3D volume from the reference image file.
# AFNI 3dLocalUnifize: This program takes an input and generates a simple "unifized" output volume.  It estimates the median in the local neighborhood of each voxel, and uses that to scale each voxel's brightness. The result is a new dataset of brightness of order 1, which still has the interesting structure(s) present in the original. This program's output looks very useful to help with dataset alignment (esp. EPI-to-anatomical) in a wide array of cases.

3dLocalUnifize \
    -input ${sbref}.nii'[0]' \
    -prefix epi_base_vol0_LU.nii

echo ---------------------------------------------------------
echo "EPI-anatomical alignment" 
echo ---------------------------------------------------------
align_epi_anat.py \
    -anat2epi -giant_move \
    -anat ${T1}_DEOB.nii \
    -suffix _al_epi3 \
    -epi epi_base_vol0_LU.nii  \
    -epi_base 0   \
    -anat_has_skull no \
    -epi_strip None -volreg off -tshift off -overwrite

rm $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi2+orig.*


echo --------------------------------------------------------------------------
echo "Compute inverse transformation from functional image to anatomical image" 
echo --------------------------------------------------------------------------
cat_matvec -ONELINE $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi3_mat.aff12.1D -I > $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi3_mat_inv.aff12.1D

echo " Convert T1-w aligned image to NIFTI from AFNI format"
3dcalc -a $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi3+orig -expr 'a' -prefix $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi3.nii -overwrite
rm $induction_dir/decoding_dice2decnef/output_brain_DEOB_al_epi3+orig.*

echo ---------------------------------------------------------
echo     "Warping of anatomical image to MNI template" 
echo  "Warped images and transformation will be in ./awpy/" 
echo ---------------------------------------------------------
# ================================= align ==================================
#auto_warp.py -base ${MNItemplate} -input ${T1}_DEOB.nii -overwrite
### new code ###
auto_warp.py \
    -base ${MNItemplate} \
    -input ${T1}_DEOB.nii \
    -skull_strip_input no \
    -overwrite
### new code ends ###

if [ ! -e ${MNItemplate} ]; then
    echo "Creating symbolic link of MNI template in current folder for visualization with AFNI"
    ln -s ${MNItemplate} .
fi

dxyz=$(3dinfo -adi epi_base_vol0_LU.nii)

echo ------------------------------------------------------------------------
echo "Warping of functional image to MNI template (catenated transformation)"
echo ------------------------------------------------------------------------
3dNwarpApply -master ./awpy/base.nii \
    -nwarp ./awpy/anat.un.aff.qw_WARP.nii ./awpy/anat.un.aff.Xat.1D output_brain_DEOB_al_epi3_mat_inv.aff12.1D \
    -source epi_base_vol0_LU.nii #${sbref}.nii \
    -prefix epi_base_vol0_LU_MNI.nii #${sbref}_MNI.nii \
    -dxyz ${dxyz} \
    -overwrite

#This needs to be done in ordee to recover the header info from the nilearn searchlight map, otherwise the warping cdoes not work
# see https://discuss.afni.nimh.nih.gov/t/afni-coregistration-of-a-searchlight-decoding-map-from-native-to-standard/8748/9

echo ------------------------------------------------------------------------
echo "Copying zero-centered search light maps and registering them to MNI space"
echo "Warping of the Searchlight map image to MNI template (catenated transformation)"
echo ------------------------------------------------------------------------

for sl in $sl_dir/*centered.nii.gz; do
filename="${sl%%.*}"

echo ------------------------------------------------------------------------
echo processing $filename
echo ------------------------------------------------------------------------

3dNwarpApply -master ./awpy/base.nii \
    -nwarp ./awpy/anat.un.aff.qw_WARP.nii ./awpy/anat.un.aff.Xat.1D output_brain_DEOB_al_epi3_mat_inv.aff12.1D \
    -source ${filename}.nii.gz \
    -prefix ${filename}_MNI.nii.gz \
    -dxyz ${dxyz} \
    -overwrite
done

echo --------------------------------
echo "----- End of script ----------"
echo --------------------------------

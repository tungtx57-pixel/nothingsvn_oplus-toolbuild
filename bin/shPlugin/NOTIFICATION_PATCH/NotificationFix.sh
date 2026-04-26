work_dir=$(pwd)
BASE_REGION=$(cat $work_dir/bin/ddevice/rom_region.txt)
android=$(cat $work_dir/bin/ddevice/androidver.txt)
version=$(cat $work_dir/bin/ddevice/rom_version.txt)

if [[ $BASE_REGION = "Domestic" ]];then
    sudo bash $work_dir/bin/shPlugin/NOTIFICATION_PATCH/xmlPatch.sh
elif [[ $BASE_REGION = "Domestic" && $android = "16" ]];then
    sudo bash $work_dir/bin/shPlugin/NOTIFICATION_PATCH/xmlPatch.sh
    sudo bash $work_dir/bin/shPlugin/NOTIFICATION_PATCH/patch.sh
else
echo "[MODS] - Not Domestic Region. Skip"
fi
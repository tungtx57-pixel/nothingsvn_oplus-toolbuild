work_dir=$(pwd)
source $work_dir/functions.sh
MAIN_FOLDER="$work_dir/build/baserom/images"
MY_STOCK="$work_dir/build/baserom/images/my_stock"
BLOB="$work_dir/bin/package/UpdateFile/COSExtenstion15"
BASE_REGION=$(cat $work_dir/bin/ddevice/rom_region.txt)
android=$(cat $work_dir/bin/ddevice/androidver.txt)

sed -i "s/persist.sys.oplus.anim_level=2/persist.sys.oplus.anim_level=1/g" $MAIN_FOLDER/my_product/build.prop

#Modify Feature
remove_feature oplus.software.startup_strategy_restrict
remove_feature com.oplus.ota.component_update_url
remove_feature com.oplus.ota.contributors_url
remove_feature com.oplus.ota.new_appointment_url
remove_feature com.oplus.ota.recruit_promote_url
remove_feature com.oplus.ota.recruit_type_url
remove_feature com.oplus.ota.pubkey
remove_feature com.oplus.ota.pubkey_ver
remove_feature com.oplus.ota.show_version_type
remove_feature com.oplus.ota.questionnaire_support
remove_feature com.android.launcher.DEFAULT_DRAWER_MODE
remove_feature com.android.settings.screen_physics_size_cm
remove_feature com.oplus.wallpapers.ai_camera_movement

if [[ $BASE_REGION == "Domestic" && $android == "15" ]]; then 
  echo "[MODS] - Replace ColorOS Shelf"
  remove_feature com.android.systemui.google_assistant_supported
  add_feature "com.android.settings.region_picker" $MAIN_FOLDER/my_product/etc/extension/com.oplus.app-features.xml
  add_feature 'com.android.systemui.google_assistant_supported" args="boolean:true' $MAIN_FOLDER/my_product/etc/extension/com.oplus.app-features.xml
  remove_feature com.oplus.smartsidebar.scene_rules_url
  remove_feature com.oplus.deepthinker.domain_name_release
  remove_feature com.oplus.deepthinker.domain_name_dev
  remove_feature com.oplusos.deepthinker.apptype.host
  remove_feature com.oplusos.deepthinker.apptype.cert_version
  remove_feature com.oplusos.deepthinker.apptype.public_key
  remove_feature com.oplus.aimemory.odin_allawntech_url
  remove_feature com.oplus.aimemory.kms_key
  remove_feature com.oplus.aimemory.export_bucket
  remove_feature com.oplus.romupdate.url
  remove_feature com.oplus.romupdate.pubkey
  remove_feature com.oplus.romupdate.pubkey_ver
  remove_feature com.oplus.romupdate.is_log_print_limit
  remove_feature com.oplus.romupdate.is_exp
  remove_feature com.oplusos.sau.url
  remove_feature com.oplusos.sau.pubkey
  remove_feature com.oplusos.sau.pubkey_ver
  remove_feature com.oplusos.sau.opex.url
  remove_feature com.oplusos.sau.opex.pubkey
  remove_feature com.oplusos.sau.opex.pubkey_ver
  remove_feature com.oplus.aiunit.tools.transmit
  cp -rf $BLOB/feature/* $MY_STOCK/etc/extension
fi
(() => {
 const dictionary = {
 en:{overview:'Overview',dashboard:'Dashboard',detector:'Disease detector',how:'How it works',system:'Detection system',ready:'Ready',classes:'Detection classes',engine:'Detection engine',analysis:'Image analysis',leaf_detector:'Rice leaf detector',upload:'Upload a leaf image',results:'Detection results',analyse:'Analyse leaf image',drop:'Drop your image here',symptoms:'Symptoms',prevention:'Prevention & Management'},
 bn:{overview:'সংক্ষিপ্ত বিবরণ',dashboard:'ড্যাশবোর্ড',detector:'রোগ শনাক্তকারী',how:'কীভাবে কাজ করে',system:'শনাক্তকরণ ব্যবস্থা',ready:'প্রস্তুত',classes:'শনাক্তকরণ শ্রেণি',engine:'শনাক্তকরণ ইঞ্জিন',analysis:'ছবি বিশ্লেষণ',leaf_detector:'ধানের পাতা শনাক্তকারী',upload:'পাতার ছবি আপলোড করুন',results:'শনাক্তকরণের ফলাফল',analyse:'পাতার ছবি বিশ্লেষণ করুন',drop:'এখানে ছবি দিন',symptoms:'লক্ষণ',prevention:'প্রতিরোধ ও ব্যবস্থাপনা'},
 hi:{overview:'अवलोकन',dashboard:'डैशबोर्ड',detector:'रोग पहचान',how:'यह कैसे काम करता है',system:'पहचान प्रणाली',ready:'तैयार',classes:'पहचान श्रेणियाँ',engine:'पहचान इंजन',analysis:'छवि विश्लेषण',leaf_detector:'धान की पत्ती पहचान',upload:'पत्ती की तस्वीर अपलोड करें',results:'पहचान परिणाम',analyse:'पत्ती की तस्वीर का विश्लेषण करें',drop:'अपनी तस्वीर यहाँ डालें',symptoms:'लक्षण',prevention:'रोकथाम और प्रबंधन'}
 };
 const selector = document.getElementById('languageSelect');
 if(!selector) return;
 const selected = localStorage.getItem('agrovision_dashboard_language');
 selector.value = dictionary[selected] ? selected : 'en';
 function render(){
  const language = selector.value;
  document.documentElement.lang=language;
  document.querySelectorAll('[data-i18n]').forEach(el => {
   const translated=dictionary[language][el.dataset.i18n];
   if(translated) el.textContent=translated;
  });
  localStorage.setItem('agrovision_dashboard_language',language);
 }
 selector.addEventListener('change',render);
 render();
})();
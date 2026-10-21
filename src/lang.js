<script>
(function(){var k='these-days-lang',v=null;try{v=localStorage.getItem(k)}catch(_){}
if(v==='th'||(!v&&/^th/i.test(navigator.language||''))){location.replace('th/'+location.hash);}
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a.sw');if(a){try{localStorage.setItem(k,a.dataset.lang)}catch(_){}}});})();
</script>

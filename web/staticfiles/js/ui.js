(function(){

function toast(title,msg,type){
  const root=document.getElementById("ds-toast-root");
  if(!root)return;

  const el=document.createElement("div");
  el.className="ds-toast";
  el.innerHTML=`<b>${title}</b><div>${msg}</div>`;
  root.appendChild(el);

  setTimeout(()=>el.remove(),3500);
}

function setLoading(el,on){
  if(!el)return;
  el.classList.toggle("ds-loading",on);
}

function validateRequired(container){
  let ok=true;
  container.querySelectorAll("[required]").forEach(inp=>{
    if(!inp.value){
      inp.classList.add("is-error");
      ok=false;
    }else{
      inp.classList.remove("is-error");
    }
  });
  return ok;
}

function money(cur,val){
  return `${cur||""} ${val||0}`;
}

window.DS_UI={toast,setLoading,validateRequired,money};

})();
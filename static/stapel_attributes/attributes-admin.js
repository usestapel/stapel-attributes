/* stapel-attributes admin — generated from static_src/, do not edit */
var ze=Object.defineProperty;var Ge=Object.getOwnPropertyDescriptor;var m=(n,t,e,i)=>{for(var s=i>1?void 0:i?Ge(t,e):t,r=n.length-1,o;r>=0;r--)(o=n[r])&&(s=(i?o(t,e,s):o(s))||s);return i&&s&&ze(t,e,s),s};var G=globalThis,K=G.ShadowRoot&&(G.ShadyCSS===void 0||G.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,ce=Symbol(),Se=new WeakMap,M=class{constructor(t,e,i){if(this._$cssResult$=!0,i!==ce)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(K&&t===void 0){let i=e!==void 0&&e.length===1;i&&(t=Se.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),i&&Se.set(e,t))}return t}toString(){return this.cssText}},we=n=>new M(typeof n=="string"?n:n+"",void 0,ce),_=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((i,s,r)=>i+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+n[r+1],n[0]);return new M(e,n,ce)},Ce=(n,t)=>{if(K)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let i=document.createElement("style"),s=G.litNonce;s!==void 0&&i.setAttribute("nonce",s),i.textContent=e.cssText,n.appendChild(i)}},pe=K?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let i of t.cssRules)e+=i.cssText;return we(e)})(n):n;var{is:Ke,defineProperty:Ye,getOwnPropertyDescriptor:Je,getOwnPropertyNames:Ze,getOwnPropertySymbols:Qe,getPrototypeOf:Xe}=Object,Y=globalThis,Ae=Y.trustedTypes,et=Ae?Ae.emptyScript:"",tt=Y.reactiveElementPolyfillSupport,D=(n,t)=>n,P={toAttribute(n,t){switch(t){case Boolean:n=n?et:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},J=(n,t)=>!Ke(n,t),ke={attribute:!0,type:String,converter:P,reflect:!1,useDefault:!1,hasChanged:J};Symbol.metadata??=Symbol("metadata"),Y.litPropertyMetadata??=new WeakMap;var S=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=ke){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let i=Symbol(),s=this.getPropertyDescriptor(t,i,e);s!==void 0&&Ye(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){let{get:s,set:r}=Je(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:s,set(o){let l=s?.call(this);r?.call(this,o),this.requestUpdate(t,l,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??ke}static _$Ei(){if(this.hasOwnProperty(D("elementProperties")))return;let t=Xe(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(D("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(D("properties"))){let e=this.properties,i=[...Ze(e),...Qe(e)];for(let s of i)this.createProperty(s,e[s])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[i,s]of e)this.elementProperties.set(i,s)}this._$Eh=new Map;for(let[e,i]of this.elementProperties){let s=this._$Eu(e,i);s!==void 0&&this._$Eh.set(s,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let i=new Set(t.flat(1/0).reverse());for(let s of i)e.unshift(pe(s))}else t!==void 0&&e.push(pe(t));return e}static _$Eu(t,e){let i=e.attribute;return i===!1?void 0:typeof i=="string"?i:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Ce(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){let i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(s!==void 0&&i.reflect===!0){let r=(i.converter?.toAttribute!==void 0?i.converter:P).toAttribute(e,i.type);this._$Em=t,r==null?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){let i=this.constructor,s=i._$Eh.get(t);if(s!==void 0&&this._$Em!==s){let r=i.getPropertyOptions(s),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:P;this._$Em=s;let l=o.fromAttribute(e,r.type);this[s]=l??this._$Ej?.get(s)??l,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(t!==void 0){let o=this.constructor;if(s===!1&&(r=this[t]),i??=o.getPropertyOptions(t),!((i.hasChanged??J)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,i))))return;this.C(t,e,i)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},o){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),s===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[s,r]of this._$Ep)this[s]=r;this._$Ep=void 0}let i=this.constructor.elementProperties;if(i.size>0)for(let[s,r]of i){let{wrapped:o}=r,l=this[s];o!==!0||this._$AL.has(s)||l===void 0||this.C(s,void 0,r,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(i=>i.hostUpdate?.()),this.update(e)):this._$EM()}catch(i){throw t=!1,this._$EM(),i}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};S.elementStyles=[],S.shadowRootOptions={mode:"open"},S[D("elementProperties")]=new Map,S[D("finalized")]=new Map,tt?.({ReactiveElement:S}),(Y.reactiveElementVersions??=[]).push("2.1.2");var ve=globalThis,Te=n=>n,Z=ve.trustedTypes,Fe=Z?Z.createPolicy("lit-html",{createHTML:n=>n}):void 0,Pe="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,Ie="?"+C,it=`<${Ie}>`,T=document,H=()=>T.createComment(""),U=n=>n===null||typeof n!="object"&&typeof n!="function",be=Array.isArray,st=n=>be(n)||typeof n?.[Symbol.iterator]=="function",ue=`[ 	
\f\r]`,I=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Re=/-->/g,Oe=/>/g,A=RegExp(`>|${ue}(?:([^\\s"'>=/]+)(${ue}*=${ue}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Le=/'/g,Me=/"/g,He=/^(?:script|style|textarea|title)$/i,ye=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),a=ye(1),xt=ye(2),Et=ye(3),F=Symbol.for("lit-noChange"),f=Symbol.for("lit-nothing"),De=new WeakMap,k=T.createTreeWalker(T,129);function Ue(n,t){if(!be(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return Fe!==void 0?Fe.createHTML(t):t}var rt=(n,t)=>{let e=n.length-1,i=[],s,r=t===2?"<svg>":t===3?"<math>":"",o=I;for(let l=0;l<e;l++){let c=n[l],d,p,u=-1,$=0;for(;$<c.length&&(o.lastIndex=$,p=o.exec(c),p!==null);)$=o.lastIndex,o===I?p[1]==="!--"?o=Re:p[1]!==void 0?o=Oe:p[2]!==void 0?(He.test(p[2])&&(s=RegExp("</"+p[2],"g")),o=A):p[3]!==void 0&&(o=A):o===A?p[0]===">"?(o=s??I,u=-1):p[1]===void 0?u=-2:(u=o.lastIndex-p[2].length,d=p[1],o=p[3]===void 0?A:p[3]==='"'?Me:Le):o===Me||o===Le?o=A:o===Re||o===Oe?o=I:(o=A,s=void 0);let E=o===A&&n[l+1].startsWith("/>")?" ":"";r+=o===I?c+it:u>=0?(i.push(d),c.slice(0,u)+Pe+c.slice(u)+C+E):c+C+(u===-2?l:E)}return[Ue(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),i]},V=class n{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,o=0,l=t.length-1,c=this.parts,[d,p]=rt(t,e);if(this.el=n.createElement(d,i),k.currentNode=this.el.content,e===2||e===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(s=k.nextNode())!==null&&c.length<l;){if(s.nodeType===1){if(s.hasAttributes())for(let u of s.getAttributeNames())if(u.endsWith(Pe)){let $=p[o++],E=s.getAttribute(u).split(C),z=/([.?@])?(.*)/.exec($);c.push({type:1,index:r,name:z[2],strings:E,ctor:z[1]==="."?he:z[1]==="?"?me:z[1]==="@"?fe:O}),s.removeAttribute(u)}else u.startsWith(C)&&(c.push({type:6,index:r}),s.removeAttribute(u));if(He.test(s.tagName)){let u=s.textContent.split(C),$=u.length-1;if($>0){s.textContent=Z?Z.emptyScript:"";for(let E=0;E<$;E++)s.append(u[E],H()),k.nextNode(),c.push({type:2,index:++r});s.append(u[$],H())}}}else if(s.nodeType===8)if(s.data===Ie)c.push({type:2,index:r});else{let u=-1;for(;(u=s.data.indexOf(C,u+1))!==-1;)c.push({type:7,index:r}),u+=C.length-1}r++}}static createElement(t,e){let i=T.createElement("template");return i.innerHTML=t,i}};function R(n,t,e=n,i){if(t===F)return t;let s=i!==void 0?e._$Co?.[i]:e._$Cl,r=U(t)?void 0:t._$litDirective$;return s?.constructor!==r&&(s?._$AO?.(!1),r===void 0?s=void 0:(s=new r(n),s._$AT(n,e,i)),i!==void 0?(e._$Co??=[])[i]=s:e._$Cl=s),s!==void 0&&(t=R(n,s._$AS(n,t.values),s,i)),t}var de=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??T).importNode(e,!0);k.currentNode=s;let r=k.nextNode(),o=0,l=0,c=i[0];for(;c!==void 0;){if(o===c.index){let d;c.type===2?d=new N(r,r.nextSibling,this,t):c.type===1?d=new c.ctor(r,c.name,c.strings,this,t):c.type===6&&(d=new ge(r,this,t)),this._$AV.push(d),c=i[++l]}o!==c?.index&&(r=k.nextNode(),o++)}return k.currentNode=T,s}p(t){let e=0;for(let i of this._$AV)i!==void 0&&(i.strings!==void 0?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}},N=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=f,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=R(this,t,e),U(t)?t===f||t==null||t===""?(this._$AH!==f&&this._$AR(),this._$AH=f):t!==this._$AH&&t!==F&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):st(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==f&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(T.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:i}=t,s=typeof i=="number"?this._$AC(t):(i.el===void 0&&(i.el=V.createElement(Ue(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{let r=new de(s,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=De.get(t.strings);return e===void 0&&De.set(t.strings,e=new V(t)),e}k(t){be(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,i,s=0;for(let r of t)s===e.length?e.push(i=new n(this.O(H()),this.O(H()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let i=Te(t).nextSibling;Te(t).remove(),t=i}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},O=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=f,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||i[0]!==""||i[1]!==""?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=f}_$AI(t,e=this,i,s){let r=this.strings,o=!1;if(r===void 0)t=R(this,t,e,0),o=!U(t)||t!==this._$AH&&t!==F,o&&(this._$AH=t);else{let l=t,c,d;for(t=r[0],c=0;c<r.length-1;c++)d=R(this,l[i+c],e,c),d===F&&(d=this._$AH[c]),o||=!U(d)||d!==this._$AH[c],d===f?t=f:t!==f&&(t+=(d??"")+r[c+1]),this._$AH[c]=d}o&&!s&&this.j(t)}j(t){t===f?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},he=class extends O{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===f?void 0:t}},me=class extends O{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==f)}},fe=class extends O{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=R(this,t,e,0)??f)===F)return;let i=this._$AH,s=t===f&&i!==f||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==f&&(i===f||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},ge=class{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){R(this,t)}};var nt=ve.litHtmlPolyfillSupport;nt?.(V,N),(ve.litHtmlVersions??=[]).push("3.3.3");var Ve=(n,t,e)=>{let i=e?.renderBefore??t,s=i._$litPart$;if(s===void 0){let r=e?.renderBefore??null;i._$litPart$=s=new N(t.insertBefore(H(),r),r,void 0,e??{})}return s._$AI(n),s};var $e=globalThis,b=class extends S{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Ve(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return F}};b._$litElement$=!0,b.finalized=!0,$e.litElementHydrateSupport?.({LitElement:b});var ot=$e.litElementPolyfillSupport;ot?.({LitElement:b});($e.litElementVersions??=[]).push("4.2.2");var at={attribute:!0,type:String,converter:P,reflect:!1,hasChanged:J},lt=(n=at,t,e)=>{let{kind:i,metadata:s}=e,r=globalThis.litPropertyMetadata.get(s);if(r===void 0&&globalThis.litPropertyMetadata.set(s,r=new Map),i==="setter"&&((n=Object.create(n)).wrapped=!0),r.set(e.name,n),i==="accessor"){let{name:o}=e;return{set(l){let c=t.get.call(this);t.set.call(this,l),this.requestUpdate(o,c,n,!0,l)},init(l){return l!==void 0&&this.C(o,void 0,n,l),l}}}if(i==="setter"){let{name:o}=e;return function(l){let c=this[o];t.call(this,l),this.requestUpdate(o,c,n,!0,l)}}throw Error("Unsupported decorator location: "+i)};function g(n){return(t,e)=>typeof e=="object"?lt(n,t,e):((i,s,r)=>{let o=s.hasOwnProperty(r);return s.constructor.createProperty(r,i),o?Object.getOwnPropertyDescriptor(s,r):void 0})(n,t,e)}function w(n){return g({...n,state:!0,attribute:!1})}var h=class extends b{constructor(){super(...arguments);this.config={type:"unknown"};this.mandatory=!1;this._value=null;this._errors=[]}static{this.styles=_`
    :host {
      display: block;
      font: var(--stapel-font, inherit);
      color: var(--stapel-color-text, #1f2430);
    }
    .ve__errors {
      display: flex;
      flex-direction: column;
      gap: var(--stapel-space-1, 4px);
      margin-top: var(--stapel-space-1, 4px);
    }
    .ve__error {
      color: var(--stapel-color-error, #d64545);
      font-size: 0.85em;
    }
    .ve__row {
      display: flex;
      flex-wrap: wrap;
      gap: var(--stapel-space-2, 8px);
      align-items: center;
    }
    button,
    input,
    select {
      font: inherit;
      color: inherit;
    }
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="month"],
    input[type="datetime-local"],
    select {
      background: var(--stapel-color-bg, #fff);
      border: 1px solid var(--stapel-color-border, #d7dbe3);
      border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-2, 8px);
    }
    input:focus-visible,
    select:focus-visible,
    button:focus-visible {
      outline: none;
      box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9);
    }
    .chip {
      cursor: pointer;
      border: 1px solid var(--stapel-color-border, #d7dbe3);
      background: var(--stapel-color-surface, #f7f8fa);
      color: var(--stapel-color-text, #1f2430);
      border-radius: var(--stapel-radius-lg, 12px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-3, 12px);
    }
    .chip--selected {
      background: var(--stapel-color-primary, #2a90d9);
      color: var(--stapel-color-primary-contrast, #fff);
      border-color: var(--stapel-color-primary, #2a90d9);
    }
  `}getValue(){return this._value}setValue(e){this._value=e,this.onValueUpdated(),this.requestUpdate()}getErrors(){return this._errors}validate(){return this._errors=[],this.mandatory&&this._value===null&&this._errors.push(this.i18n.t("admin.attributes.required")),this._value!==null&&this._errors.push(...this.validateValue()),this._errors}validateValue(){return[]}onValueUpdated(){}emit(){this.validate(),this.requestUpdate(),this.onValueChange?.(this._value,this._errors),this.dispatchEvent(new CustomEvent("value-change",{detail:{value:this._value,errors:this._errors},bubbles:!0,composed:!0}))}render(){return a`
      <div class="ve" part="editor">${this.renderInput()}</div>
      <div class="ve__errors">
        ${this._errors.map(e=>a`<span class="ve__error">${e}</span>`)}
      </div>
    `}};m([g({attribute:!1})],h.prototype,"config",2),m([g({attribute:!1})],h.prototype,"mandatory",2),m([g({attribute:!1})],h.prototype,"i18n",2),m([w()],h.prototype,"_value",2),m([w()],h.prototype,"_errors",2);function y(n){return t=>{let e=new n;return e.config=t.config,e.mandatory=t.mandatory??!1,e.i18n=t.i18n,e.onValueChange=t.onChange,t.initialValue!==void 0&&e.setValue(t.initialValue??null),e}}var _e=new Map,Ne=new Map;function v(n,t){_e.set(n,t)}function ct(n,t){Ne.set(n,t)}function X(n){return n&&_e.get(n)||pt}var pt=n=>{let t=document.createElement("div");return t.className="value-editor value-editor--unsupported",t.textContent=n.i18n.t("admin.attributes.unsupported_type",{type:n.config?.type??"unknown"}),t.getValue=()=>null,t};function ut(){return[..._e.keys()].sort()}function dt(){return[...Ne.keys()].sort()}function qe(){let n={registerValueEditor:v,registerConfigWidget:ct,registeredValueEditorTypes:ut,registeredConfigWidgetKinds:dt};return typeof window<"u"&&(window.StapelAttributes=n),n}var ee=class extends h{get current(){return this._value?this._value.value:null}setBool(t){this.current===t&&!this.mandatory?this._value=null:this._value={type:"bool",value:t},this.emit()}renderInput(){let t=String(this.config.trueLabel??"Yes");if(this.mandatory){let e=String(this.config.falseLabel??"No");return a`
        <div class="ve__row">
          <button
            type="button"
            class="chip ${this.current===!0?"chip--selected":""}"
            @click=${()=>this.setBool(!0)}
          >${t}</button>
          <button
            type="button"
            class="chip ${this.current===!1?"chip--selected":""}"
            @click=${()=>this.setBool(!1)}
          >${e}</button>
        </div>
      `}return a`
      <label class="ve__row" style="cursor: pointer">
        <input
          type="checkbox"
          .checked=${this.current===!0}
          @change=${e=>{this._value=e.target.checked?{type:"bool",value:!0}:null,this.emit()}}
        />
        <span>${t}</span>
      </label>
    `}};typeof customElements<"u"&&!customElements.get("stapel-ve-bool")&&customElements.define("stapel-ve-bool",ee);v("bool",y(ee));var te="__custom__",q=class extends h{constructor(){super(...arguments);this._customMode=!1;this._singleApplied=!1}get type(){return this.config.type||"string"}get options(){return this.config.options||[]}get allowCustom(){return this.config.allowCustom!==!1}optVal(e){return typeof e=="object"?e.value:e}optLabel(e){return String(typeof e=="object"?e.label??e.value:e)}parse(e){if(this.type==="int"){let i=parseInt(e,10);return isNaN(i)?null:i}if(this.type==="float"){let i=parseFloat(e);return isNaN(i)?null:i}return e}setFromRaw(e){let i=e.trim();if(i==="")this._value=null;else{let s=this.parse(i);this._value=s!==null?{type:this.type,value:s}:null}this.emit()}get current(){return this._value?this._value.value:null}inOptions(e){return this.options.some(i=>String(this.optVal(i))===String(e))}willUpdate(){this.options.length===1&&!this.allowCustom&&!this._singleApplied&&this._value===null&&(this._singleApplied=!0,this._value={type:this.type,value:this.parse(String(this.optVal(this.options[0])))})}validateValue(){let e=[],i=this.current;if(i===null)return e;if(this.type==="int"||this.type==="float"){let s=i;this.config.min!=null&&s<this.config.min&&e.push(`Minimum value is ${this.config.min}`),this.config.max!=null&&s>this.config.max&&e.push(`Maximum value is ${this.config.max}`)}else{let s=i;this.config.minLength!=null&&s.length<this.config.minLength&&e.push(`Minimum length is ${this.config.minLength}`),this.config.maxLength!=null&&s.length>this.config.maxLength&&e.push(`Maximum length is ${this.config.maxLength}`),this.config.pattern&&!new RegExp(this.config.pattern).test(s)&&e.push("Invalid format")}return e}renderPlainInput(){let e=this.type==="string",i=this.type==="int"?"1":this.type==="float"?String(Math.pow(10,-(this.config.precision??2))):void 0,s=this.type==="int"||this.type==="float"?this.options:[];return a`
      <div class="ve__row">
        ${this.config.prefix?a`<span>${this.config.prefix}</span>`:""}
        <input
          type=${e?"text":"number"}
          .value=${this.current??""}
          placeholder=${this.config.placeholder?String(this.config.placeholder):""}
          step=${i??""}
          min=${this.config.min!=null?String(this.config.min):""}
          max=${this.config.max!=null?String(this.config.max):""}
          @input=${r=>this.setFromRaw(r.target.value)}
        />
        ${this.config.postfix?a`<span>${this.config.postfix}</span>`:""}
      </div>
      ${s.length?a`<div class="ve__row">${s.map(r=>a`
        <button type="button" class="chip" @click=${()=>this.setFromRaw(String(this.optVal(r)))}>${this.optLabel(r)}</button>`)}
      </div>`:""}
    `}renderDropdown(e){let i=this.current,s=this.options.length===1&&!e,r=this._customMode?te:i===null?"":this.inOptions(i)?String(i):e?te:"",o=this.type==="int"?"1":this.type==="float"?String(Math.pow(10,-(this.config.precision??2))):void 0;return a`
      <div class="ve__row" style="flex-direction: column; align-items: stretch">
        <select ?disabled=${s} .value=${s?String(this.optVal(this.options[0])):r}
          @change=${l=>this.onSelect(l.target.value)}>
          ${s?"":a`<option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>`}
          ${this.options.map(l=>a`<option value=${String(this.optVal(l))}>${this.optLabel(l)}</option>`)}
          ${e?a`<option value=${te}>${this.i18n.t("admin.attributes.other")}</option>`:""}
        </select>
        ${e&&this._customMode?a`
          <input type=${this.type==="string"?"text":"number"} step=${o??""}
            .value=${i!==null&&!this.inOptions(i)?String(i):""}
            placeholder=${this.i18n.t("admin.attributes.other")}
            @input=${l=>this.setFromRaw(l.target.value)} />`:""}
      </div>
    `}onSelect(e){if(e===te){this._customMode=!0,this.requestUpdate();return}this._customMode=!1,e===""?this._value=null:this._value={type:this.type,value:this.parse(e)},this.emit()}renderInput(){return this.options.length===0?this.renderPlainInput():this.allowCustom?this.renderDropdown(!0):this.renderDropdown(!1)}};m([w()],q.prototype,"_customMode",2);typeof customElements<"u"&&!customElements.get("stapel-ve-string-number")&&customElements.define("stapel-ve-string-number",q);for(let n of["string","int","float"])v(n,y(q));var ie=class extends h{static{this.styles=[h.styles,_`
      .ve__header {
        font-weight: 600;
        color: var(--stapel-color-text, #1f2430);
        border-bottom: 1px solid var(--stapel-color-border, #d7dbe3);
        padding-bottom: var(--stapel-space-1, 4px);
      }
      .ve__header--l { font-size: 1.3em; }
      .ve__header--m { font-size: 1.1em; }
    `]}getValue(){return null}validate(){return this._errors=[],this._errors}renderInput(){let t=String(this.config.style??"l"),e=String(this.config.title??this.config.name??"Section");return a`<div class="ve__header ve__header--${t}">${e}</div>`}};typeof customElements<"u"&&!customElements.get("stapel-ve-header")&&customElements.define("stapel-ve-header",ie);v("header",y(ie));var se=class extends h{get options(){return this.config.options||[]}get selected(){return this._value&&Array.isArray(this._value.value)?[...this._value.value]:[]}get maxSelected(){return this.config.maxSelected}label(t){return String(t.label??t.value)}setSelected(t){this._value=t.length===0?null:{type:"select",value:t},this.emit()}toggle(t){let e=this.selected,i=e.indexOf(t);if(i>=0){e.splice(i,1),this.setSelected(e);return}if(this.maxSelected===1){this.setSelected([t]);return}this.maxSelected&&e.length>=this.maxSelected||(e.push(t),this.setSelected(e))}validateValue(){let t=[],e=this.selected.length,i=this.config.minSelected||0;return e>0&&e<i&&t.push(`Select at least ${i} option(s)`),this.maxSelected&&e>this.maxSelected&&t.push(`Select at most ${this.maxSelected} option(s)`),t}validate(){this._errors=[];let t=this.selected.length;return this.mandatory&&t===0?(this._errors.push(this.i18n.t("admin.attributes.required")),this._errors):(this._errors.push(...this.validateValue()),this._errors)}renderChips(){let t=this.selected;return a`<div class="ve__row">
      ${this.options.map(e=>a`
        <button type="button" class="chip ${t.includes(e.value)?"chip--selected":""}"
          @click=${()=>this.toggle(e.value)}>
          ${e.icon?a`<img src=${e.icon} width="16" height="16" style="vertical-align:middle;margin-right:4px" />`:""}${this.label(e)}
        </button>`)}
    </div>`}renderCheckboxes(){let t=this.selected;return a`<div class="ve__row" style="flex-direction:column;align-items:flex-start">
      ${this.options.map(e=>a`
        <label class="ve__row" style="cursor:pointer">
          <input type="checkbox" .checked=${t.includes(e.value)} @change=${()=>this.toggle(e.value)} />
          <span>${this.label(e)}</span>
        </label>`)}
    </div>`}renderDropdown(){let t=this.selected;if(this.maxSelected===1)return a`<select .value=${t[0]??""} @change=${i=>{let s=i.target.value;this.setSelected(s?[s]:[])}}>
        <option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>
        ${this.options.map(i=>a`<option value=${i.value}>${this.label(i)}</option>`)}
      </select>`;let e=this.options.filter(i=>!t.includes(i.value));return a`<div class="ve__row" style="flex-direction:column;align-items:stretch">
      <select .value=${""} @change=${i=>{let s=i.target.value;s&&this.setSelected([...t,s])}}>
        <option value="">${this.i18n.t("admin.attributes.add")}</option>
        ${e.map(i=>a`<option value=${i.value}>${this.label(i)}</option>`)}
      </select>
      ${t.length?a`<div class="ve__row">${t.map(i=>{let s=this.options.find(r=>r.value===i);return a`<span class="chip chip--selected">${s?this.label(s):i}
          <button type="button" style="background:none;border:none;cursor:pointer;color:inherit"
            @click=${()=>this.toggle(i)}>×</button></span>`})}</div>`:""}
    </div>`}renderInput(){switch(this.config.uiStyle){case"checkboxes":return this.renderCheckboxes();case"dropdown":return this.renderDropdown();default:return this.renderChips()}}};typeof customElements<"u"&&!customElements.get("stapel-ve-select")&&customElements.define("stapel-ve-select",se);v("select",y(se));var re=class extends h{get precision(){return this.config.precision||"date"}get ts(){return this._value?this._value.value:null}tsToInput(t,e){let i=new Date(t*1e3);switch(e){case"year":return i.getFullYear().toString();case"month":return i.toISOString().substring(0,7);case"datetime":return i.toISOString().substring(0,16);default:return i.toISOString().substring(0,10)}}inputToTs(t,e){let i;switch(e){case"year":i=new Date(parseInt(t,10),0,1);break;case"month":i=new Date(t+"-01");break;default:i=new Date(t);break}return Math.floor(i.getTime()/1e3)}formatTs(t,e){let i=new Date(t*1e3);switch(e){case"year":return i.getFullYear().toString();case"month":return i.toLocaleDateString(void 0,{year:"numeric",month:"short"});case"datetime":return i.toLocaleString();default:return i.toLocaleDateString()}}onInput(t){this._value=t?{type:"date",value:this.inputToTs(t,this.precision)}:null,this.emit()}validateValue(){let t=[],e=this.ts;if(e===null)return t;let i=Math.floor(Date.now()/1e3);return this.config.minDate!=null&&e<this.config.minDate&&t.push("Date is too early"),this.config.maxDate!=null&&e>this.config.maxDate&&t.push("Date is too late"),this.config.allowFuture===!1&&e>i&&t.push("Future dates not allowed"),this.config.allowPast===!1&&e<i&&t.push("Past dates not allowed"),t}renderInput(){let t=this.precision,e=t==="year"?"number":t==="month"?"month":t==="datetime"?"datetime-local":"date",i=this.ts!==null?this.tsToInput(this.ts,t):"",s=this.config.minDate&&t!=="year"?this.tsToInput(this.config.minDate,t):"",r=this.config.maxDate&&t!=="year"?this.tsToInput(this.config.maxDate,t):"",o=this.config.options||[];return a`
      <input
        type=${e}
        .value=${i}
        min=${t==="year"?"1900":s}
        max=${t==="year"?"2100":r}
        placeholder=${t==="year"?"YYYY":String(this.config.placeholder??"")}
        @change=${l=>this.onInput(l.target.value)}
      />
      ${o.length?a`<div class="ve__row">${o.map(l=>a`
        <button type="button" class="chip" @click=${()=>{this._value={type:"date",value:l},this.emit()}}>
          ${this.formatTs(l,t)}</button>`)}
      </div>`:""}
    `}};typeof customElements<"u"&&!customElements.get("stapel-ve-date")&&customElements.define("stapel-ve-date",re);v("date",y(re));var ne=["black","white","gray","silver","red","pink","orange","yellow","green","blue","purple","brown","gold","beige","turquoise","clear","multicolor","custom"],je={black:"#222222",white:"#FFFFFF",gray:"#A0A0A0",silver:"linear-gradient(135deg, #797979 10%, #FFFFFF 60%, #C0C0C0 100%)",red:"#F35555",pink:"#FFC0CB",orange:"#FFA500",yellow:"#FFFF00",green:"#0ED70E",blue:"#4285F4",purple:"#8A73FF",brown:"#B1662A",gold:"linear-gradient(135deg, #F1A100 10%, #FFF4AD 60%, #FFC200 100%)",beige:"#DDCEBA",turquoise:"#4DC7C2",clear:"linear-gradient(135deg, #FFFFFF 40%, #E1E1E1 50%, #FFFFFF 60%)",multicolor:"linear-gradient(135deg, #FF6B6B 20%, #FF9E4D 30%, #FFE75A 40%, #6EE87A 50%, #63D8FF 60%, #5C7CFF 70%, #C07CFF 80%)",custom:"conic-gradient(red, yellow, lime, aqua, blue, magenta, red)"};function L(n){return n.hex?n.hex:n.simple&&je[n.simple]?je[n.simple]:"#CCCCCC"}function oe(n){return!!n&&n.includes("gradient")}var ae=class extends h{constructor(){super(...arguments);this._locked=!1}static{this.styles=[h.styles,_`
      .swatches { display: flex; flex-wrap: wrap; gap: var(--stapel-space-3, 12px); }
      .swatch { display: flex; flex-direction: column; align-items: center; gap: var(--stapel-space-1, 4px); width: 56px; }
      .circle {
        width: 32px; height: 32px; border-radius: 50%;
        border: 1px solid var(--stapel-color-border, #d7dbe3);
        cursor: pointer; position: relative; padding: 0;
      }
      .circle--selected { box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9); }
      .check { position: absolute; inset: 0; display: grid; place-items: center; color: #fff; }
      .name { font-size: 0.8em; color: var(--stapel-color-text-muted, #6b7280); text-align: center; }
    `]}willUpdate(){let e=this.config.options||[];e.length===1&&!this.config.allowCustom&&this._value===null&&!this._locked&&(this._locked=!0,this._value={type:"hex_color",value:this.copyConfigFields(e[0])})}copyConfigFields(e){let i={};return e.simple!==void 0&&(i.simple=e.simple),e.hex!==void 0&&(i.hex=e.hex),e.label!==void 0&&(i.label=e.label),i}displayOptions(){let e=this.config.options||[];return e.length===0?ne.filter(i=>i!=="custom").map(i=>({simple:i,_displayLabel:i.charAt(0).toUpperCase()+i.slice(1)})):e}get current(){return this._value?this._value.value:null}isExactMatch(e,i){if(!i||(e.simple||null)!==(i.simple||null))return!1;let s=e.hex?e.hex.toLowerCase():null,r=i.hex?i.hex.toLowerCase():null;return!(s!==r||(e.label||null)!==(i.label||null))}select(e,i){this._value=i?null:{type:"hex_color",value:this.copyConfigFields(e)},this.emit()}validateValue(){let e=this.current?.hex;return e&&!/^#[0-9A-Fa-f]{6}$/.test(e)&&!/^#[0-9A-Fa-f]{3}$/.test(e)?["Invalid hex color format"]:[]}renderInput(){let e=this.current,i=["white","beige","yellow","clear"];return a`
      <div class="swatches">
        ${this.displayOptions().map(s=>{let r=this.isExactMatch(s,e),o=L(s),l=s.label??s._displayLabel??s.simple??"",c=oe(o)?`background:${o}`:`background-color:${o}`;return a`<div class="swatch">
            <button type="button" class="circle ${r?"circle--selected":""}"
              style=${c} ?disabled=${this._locked}
              @click=${()=>this.select(s,r)}>
              ${r?a`<span class="check" style=${i.includes(s.simple??"")?"color:#333":""}>✓</span>`:""}
            </button>
            <span class="name">${l}</span>
          </div>`})}
      </div>
      ${this.config.allowCustom?a`
        <div class="ve__row" style="margin-top:var(--stapel-space-2,8px)">
          <input type="color" .value=${e?.hex??"#000000"} @change=${s=>{this._value={type:"hex_color",value:{simple:"custom",hex:s.target.value}},this.emit()}} />
        </div>`:""}
    `}};typeof customElements<"u"&&!customElements.get("stapel-ve-hex-color")&&customElements.define("stapel-ve-hex-color",ae);v("hex_color",y(ae));var j=class extends h{constructor(){super(...arguments);this._path=[];this._locked=new Set;this._autoRan=!1}get options(){return this.config.options||[]}onValueUpdated(){this._path=this._value&&Array.isArray(this._value.value)?[...this._value.value]:[],this._autoRan=!1}willUpdate(){this._autoRan||(this._autoRan=!0,this.autoSelectSingleOptions(),this.setValueFromPath())}autoSelectSingleOptions(){this._locked.clear();let e=this.options,i=0;for(;e&&e.length>0;)if(e.length===1){let s=e[0];if(this._path[i]=s.value,this._locked.add(i),s.children&&s.children.length>0)e=s.children,i++;else break}else{let s=this._path[i];if(s){let r=e.find(o=>o.value===s);if(r&&r.children&&r.children.length>0){e=r.children,i++;continue}}break}}autoSelectChildrenFromDepth(e){for(let r of[...this._locked])r>=e&&this._locked.delete(r);let i=this.options,s=0;for(;s<e&&i.length>0;){let r=this._path[s];if(!r)return;let o=i.find(l=>l.value===r);if(!o||!o.children)return;i=o.children,s++}for(;i&&i.length===1;){let r=i[0];if(this._path[s]=r.value,this._locked.add(s),r.children&&r.children.length>0)i=r.children,s++;else break}}onLevelChange(e,i){i===""?this._path=this._path.slice(0,e):(this._path=this._path.slice(0,e),this._path[e]=i),this.autoSelectChildrenFromDepth(e+1),this.setValueFromPath(),this.requestUpdate()}setValueFromPath(){this._value=this._path.length===0?null:{type:"hierarchical_select",value:[...this._path]},this.emit()}validate(){this._errors=[];let e=this._path.length;if(this.mandatory&&e===0)return this._errors.push(this.i18n.t("admin.attributes.required")),this._errors;let i=this.config.minDepth||1,s=this.config.maxDepth;return e>0&&e<i&&this._errors.push(`Select at least ${i} level(s)`),s&&e>s&&this._errors.push(`Select at most ${s} level(s)`),this._errors}renderInput(){let e=[],i=this.options,s=null,r=0;for(;i&&i.length>0;){let o=this._path[r],l=this._locked.has(r),c=r,d=i;if(e.push(a`
        <div class="ve__row" style="flex-direction:column;align-items:flex-start">
          ${s?a`<span style="color:var(--stapel-color-text-muted,#6b7280)">${s}</span>`:""}
          <select ?disabled=${l} .value=${o??""}
            @change=${p=>this.onLevelChange(c,p.target.value)}>
            ${l?"":a`<option value="">${this.i18n.t("admin.attributes.select_placeholder")}</option>`}
            ${d.map(p=>a`<option value=${p.value}>${p.label??p.value}</option>`)}
          </select>
        </div>`),o){let p=i.find(u=>u.value===o);if(p&&p.children&&p.children.length>0){i=p.children,s=p.childrenTitle??null,r++;continue}}break}return a`<div class="ve__row" style="flex-direction:column;align-items:stretch">${e}</div>`}};m([w()],j.prototype,"_path",2);typeof customElements<"u"&&!customElements.get("stapel-ve-hierarchical")&&customElements.define("stapel-ve-hierarchical",j);v("hierarchical_select",y(j));function xe(n){return n.toLowerCase().replace(/\s+/g,"_").replace(/[^\p{L}\p{N}_]/gu,"")}function Ee(n,t){return t&&n.startsWith(t)?n.substring(t.length):n}var x=class extends b{constructor(){super(...arguments);this.declaration={label_key:"",fields:[]};this.prefixName="";this.translateMode="all";this.typeSlug="";this.data={};this.manual=new Set}static{this.styles=_`
    :host { display: block; color: var(--stapel-color-text, #1f2430); font: var(--stapel-font, inherit); }
    .field { margin-bottom: var(--stapel-space-3, 12px); }
    label.hd { display: block; font-weight: 600; margin-bottom: var(--stapel-space-1, 4px); }
    .req { color: var(--stapel-color-error, #d64545); }
    .row { display: flex; gap: var(--stapel-space-2, 8px); align-items: center; margin-bottom: var(--stapel-space-1, 4px); }
    input[type="text"], input[type="number"], input[type="datetime-local"], select {
      background: var(--stapel-color-bg, #fff); color: inherit;
      border: 1px solid var(--stapel-color-border, #d7dbe3); border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-1, 4px) var(--stapel-space-2, 8px); font: inherit;
    }
    input:focus-visible, select:focus-visible, button:focus-visible {
      outline: none; box-shadow: var(--stapel-focus-ring, 0 0 0 2px #fff, 0 0 0 4px #2a90d9);
    }
    .btn {
      cursor: pointer; border: 1px solid var(--stapel-color-border, #d7dbe3);
      background: var(--stapel-color-surface, #f7f8fa); color: inherit;
      border-radius: var(--stapel-radius-sm, 4px); padding: 2px var(--stapel-space-2, 8px);
    }
    .swatch { width: 20px; height: 20px; border-radius: 50%; border: 1px solid var(--stapel-color-border, #d7dbe3); }
    .nested { margin-left: var(--stapel-space-4, 16px); border-left: 2px solid var(--stapel-color-border, #d7dbe3); padding-left: var(--stapel-space-2, 8px); }
  `}willUpdate(e){e.has("declaration")&&this.seedData()}setConfig(e){if(this.data={},this.manual.clear(),e)for(let[i,s]of Object.entries(e))i!=="type"&&(this.data[i]=s);this.seedData(),this.requestUpdate()}seedData(){for(let e of this.declaration.fields){let i=this.data[e.name];["number_options","string_options","timestamp_array"].includes(e.kind)?this.data[e.name]=Array.isArray(i)?[...i]:[]:["color_options","select_options_with_default"].includes(e.kind)?this.data[e.name]=Array.isArray(i)?i.map(s=>({...s})):[]:e.kind==="hierarchical_options"&&(this.data[e.name]=Array.isArray(i)?JSON.parse(JSON.stringify(i)):[])}}optionPrefix(){return this.translateMode==="all"&&this.prefixName?this.prefixName+".":""}emit(){this.requestUpdate(),this.onConfigChange?.(this.getConfig())}getConfig(){let e={type:this.typeSlug};for(let i of this.declaration.fields){let s=this.fieldValue(i);i.kind==="max_selected_dropdown"?s!==void 0&&(e[i.name]=s):s!=null&&s!==""&&(e[i.name]=s)}return e}fieldValue(e){let i=this.data[e.name];switch(e.kind){case"number_options":return i?.filter(s=>s!=null&&s!=="");case"string_options":return i?.filter(s=>s!=null&&s!=="");case"timestamp_array":return i?.filter(s=>s!==null);case"color_options":return i?.filter(s=>s.hex||s.label||s.simple);case"select_options_with_default":return i?.filter(s=>s.value);case"hierarchical_options":return this.filterNodes(i||[]);case"max_selected_dropdown":{let s=this.data[e.name];return s===""?null:s===void 0?void 0:parseInt(String(s),10)}case"checkbox":return i===void 0?e.default??!1:!!i;case"number":return i===void 0||i===""?void 0:e.params?.step===1?parseInt(String(i),10):parseFloat(String(i));default:return i===""?void 0:i}}filterNodes(e){let i=[];for(let s of e){if(!s.value)continue;let r={value:s.value};s.label&&(r.label=s.label),s.icon&&(r.icon=s.icon),s.childrenTitle&&(r.childrenTitle=s.childrenTitle);let o=this.filterNodes(s.children||[]);o.length>0&&(r.children=o),i.push(r)}return i}render(){return a`${this.declaration.fields.map(e=>a`
      <div class="field">
        <label class="hd">${this.i18n.t(e.label_key)}${e.required?a`<span class="req"> *</span>`:""}</label>
        ${this.renderKind(e)}
      </div>`)}`}renderKind(e){switch(e.kind){case"number":return this.renderNumber(e);case"text":case"translatable_text":return this.renderText(e);case"checkbox":return this.renderCheckbox(e);case"select":return this.renderSelect(e);case"timestamp":return this.renderTimestamp(e);case"number_options":return this.renderScalarList(e,"number");case"string_options":return this.renderScalarList(e,"text");case"timestamp_array":return this.renderTimestampArray(e);case"color_options":return this.renderColorOptions(e);case"select_options_with_default":return this.renderSelectOptions(e);case"max_selected_dropdown":return this.renderMaxSelected(e);case"hierarchical_options":return this.renderHierarchical(e);default:return this.renderText(e)}}renderNumber(e){let i=this.data[e.name]??e.default??"";return a`<input type="number" step=${e.params?.step??1} .value=${String(i)}
      @input=${s=>{this.data[e.name]=s.target.value,this.emit()}} />`}renderText(e){return a`<input type="text" .value=${String(this.data[e.name]??"")}
      placeholder=${e.params?.placeholder??""}
      @input=${i=>{this.data[e.name]=i.target.value,this.emit()}} />`}renderCheckbox(e){let i=this.data[e.name]===void 0?!!e.default:!!this.data[e.name];return a`<input type="checkbox" .checked=${i}
      @change=${s=>{this.data[e.name]=s.target.checked,this.emit()}} />`}renderSelect(e){let i=this.data[e.name],s=e.params?.options||[];return a`<select @change=${r=>{this.data[e.name]=r.target.value,this.emit()}}>
      ${s.map(r=>a`<option value=${r.value} ?selected=${i===r.value||!i&&e.default===r.value}>${r.label}</option>`)}
    </select>`}renderTimestamp(e){let i=this.data[e.name],s=i!=null?new Date(i*1e3).toISOString().slice(0,16):"";return a`<div class="row">
      <input type="datetime-local" .value=${s} @change=${r=>{let o=r.target.value;this.data[e.name]=o?Math.floor(new Date(o).getTime()/1e3):void 0,this.emit()}} />
      <button type="button" class="btn" @click=${()=>{this.data[e.name]=void 0,this.emit()}}>${this.i18n.t("admin.attributes.clear")}</button>
    </div>`}moveRow(e,i,s){if(s<0||s>=e.length||i===s)return;let[r]=e.splice(i,1);e.splice(s,0,r)}reorderControls(e,i){return a`
      <button type="button" class="btn" aria-label=${this.i18n.t("admin.attributes.move_up")}
        ?disabled=${i===0} @click=${()=>{this.moveRow(e,i,i-1),this.emit()}}>↑</button>
      <button type="button" class="btn" aria-label=${this.i18n.t("admin.attributes.move_down")}
        ?disabled=${i===e.length-1} @click=${()=>{this.moveRow(e,i,i+1),this.emit()}}>↓</button>`}renderScalarList(e,i){let s=this.data[e.name]||[];return a`<div>
      ${s.map((r,o)=>a`<div class="row">
        <input type=${i} .value=${r==null?"":String(r)} @input=${l=>{let c=l.target.value;s[o]=i==="number"?c===""?null:parseFloat(c):c,this.emit()}} />
        ${this.reorderControls(s,o)}
        <button type="button" class="btn" @click=${()=>{s.splice(o,1),this.emit()}}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${()=>{s.push(i==="number"?null:""),this.requestUpdate()}}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`}renderTimestampArray(e){let i=this.data[e.name]||[];return a`<div>
      ${i.map((s,r)=>a`<div class="row">
        <input type="datetime-local" .value=${s!=null?new Date(s*1e3).toISOString().slice(0,16):""}
          @change=${o=>{let l=o.target.value;i[r]=l?Math.floor(new Date(l).getTime()/1e3):null,this.emit()}} />
        ${this.reorderControls(i,r)}
        <button type="button" class="btn" @click=${()=>{i.splice(r,1),this.emit()}}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${()=>{let s=new Date().getUTCFullYear();i.push(Math.floor(Date.UTC(s,0,1,12,0,0)/1e3)),this.emit()}}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`}renderColorOptions(e){let i=this.data[e.name]||[];return a`<div>
      ${i.map((s,r)=>a`<div class="row">
        <span class="swatch" style=${oe(L(s))?`background:${L(s)}`:`background-color:${L(s)}`}></span>
        <select @change=${o=>{s.simple=o.target.value,this.emit()}}>
          <option value="">${this.i18n.t("admin.attributes.simple_placeholder")}</option>
          ${ne.map(o=>a`<option value=${o} ?selected=${s.simple===o}>${o}</option>`)}
        </select>
        <input type="text" placeholder="#RRGGBB" .value=${String(s.hex??"")} @input=${o=>{s.hex=o.target.value,this.emit()}} />
        <input type="text" placeholder="label" .value=${String(s.label??"")} @input=${o=>{s.label=o.target.value,this.emit()}} />
        ${this.reorderControls(i,r)}
        <button type="button" class="btn" @click=${()=>{i.splice(r,1),this.emit()}}>×</button>
      </div>`)}
      <button type="button" class="btn" @click=${()=>{i.push({hex:"",label:"",simple:""}),this.requestUpdate()}}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`}renderSelectOptions(e){let i=this.data[e.name]||[],s=this.optionPrefix();return a`<div>
      ${i.map((r,o)=>{let l=`${e.name}_${o}`;return a`<div class="row">
          <input type="text" placeholder="label" .value=${String(r.label??"")} @input=${c=>{let d=c.target.value;r.label=d,this.manual.has(l)||(r.value=xe(Ee(d,s))),this.emit()}} />
          <input type="text" placeholder="value" .value=${String(r.value??"")} @input=${c=>{r.value=c.target.value,this.manual.add(l),this.emit()}} />
          <label class="row"><input type="checkbox" .checked=${!!r.default} @change=${c=>{r.default=c.target.checked,this.emit()}} /> def</label>
          ${this.reorderControls(i,o)}
          <button type="button" class="btn" @click=${()=>{i.splice(o,1),this.manual.delete(l),this.emit()}}>×</button>
        </div>`})}
      <button type="button" class="btn" @click=${()=>{i.push({value:"",label:"",default:!1}),this.requestUpdate()}}>+ ${this.i18n.t("admin.attributes.add")}</button>
    </div>`}renderMaxSelected(e){let i=this.data.options||[],s=Math.max(i.length,1),r=this.data[e.name],o=r!=null?String(r):e.default!==void 0?String(e.default):"1";return a`<select @change=${l=>{this.data[e.name]=l.target.value,this.emit()}}>
      ${Array.from({length:s},(l,c)=>c+1).map(l=>a`<option value=${String(l)} ?selected=${o===String(l)}>${l}${l===1?" "+this.i18n.t("admin.attributes.single_select"):""}</option>`)}
      <option value="" ?selected=${o===""}>${this.i18n.t("admin.attributes.unlimited")}</option>
    </select>`}renderHierarchical(e,i,s=""){let r=i??(this.data[e.name]||[]),o=this.optionPrefix();return a`<div>
      ${r.map((l,c)=>{let d=s===""?String(c):`${s}.${c}`,p=`${e.name}_${d}`,u=l.children||[];return a`<div>
          <div class="row">
            ${s?a`<span>↳</span>`:""}
            <input type="text" placeholder="label" .value=${String(l.label??"")} @input=${$=>{let E=$.target.value;l.label=E,this.manual.has(p)||(l.value=xe(Ee(E,o))),this.emit()}} />
            <input type="text" placeholder="value" .value=${String(l.value??"")} @input=${$=>{l.value=$.target.value,this.manual.add(p),this.emit()}} />
            ${this.reorderControls(r,c)}
            <button type="button" class="btn" @click=${()=>{l.children||(l.children=[]),l.children.push({value:"",label:"",children:[]}),this.emit()}}>+ child</button>
            <button type="button" class="btn" @click=${()=>{r.splice(c,1),this.emit()}}>×</button>
          </div>
          ${u.length?a`<div class="nested">${this.renderHierarchical(e,u,d)}</div>`:""}
        </div>`})}
      ${s===""?a`<button type="button" class="btn" @click=${()=>{r.push({value:"",label:"",children:[]}),this.requestUpdate()}}>+ ${this.i18n.t("admin.attributes.add")}</button>`:""}
    </div>`}};m([g({attribute:!1})],x.prototype,"declaration",2),m([g({attribute:!1})],x.prototype,"i18n",2),m([g({attribute:!1})],x.prototype,"prefixName",2),m([g({attribute:!1})],x.prototype,"translateMode",2),m([g({attribute:!1})],x.prototype,"typeSlug",2),m([w()],x.prototype,"data",2);typeof customElements<"u"&&!customElements.get("stapel-config-editor")&&customElements.define("stapel-config-editor",x);var le=class extends b{constructor(){super(...arguments);this._onKey=e=>{e.key==="Escape"&&this.close()}}static{this.styles=_`
    .overlay {
      position: fixed; inset: 0; background: var(--stapel-color-overlay, rgba(20, 24, 33, 0.45));
      display: grid; place-items: center; z-index: 1000; padding: var(--stapel-space-4, 16px);
    }
    .dialog {
      background: var(--stapel-color-bg, #fff); color: var(--stapel-color-text, #1f2430);
      border-radius: var(--stapel-radius-lg, 12px); box-shadow: var(--stapel-elevation-2, 0 4px 12px rgba(0,0,0,.16));
      max-width: min(560px, 100%); max-height: 90vh; overflow: auto; padding: var(--stapel-space-5, 24px);
    }
  `}connectedCallback(){super.connectedCallback(),document.addEventListener("keydown",this._onKey)}disconnectedCallback(){super.disconnectedCallback(),document.removeEventListener("keydown",this._onKey)}close(){this.dispatchEvent(new CustomEvent("close",{bubbles:!0,composed:!0})),this.remove()}render(){return a`
      <div class="overlay" @click=${e=>{e.target===e.currentTarget&&this.close()}}>
        <div class="dialog" role="dialog" aria-modal="true"><slot></slot></div>
      </div>
    `}};typeof customElements<"u"&&!customElements.get("stapel-dialog")&&customElements.define("stapel-dialog",le);function We(n){let t=new le;return t.appendChild(n),document.body.appendChild(t),()=>t.close()}var W=class extends b{constructor(){super(...arguments);this.envelope=null}static{this.styles=_`
    .err {
      color: var(--stapel-color-error, #d64545);
      background: var(--stapel-color-error-bg, #fdecec);
      border: 1px solid var(--stapel-color-error, #d64545);
      border-radius: var(--stapel-radius-sm, 4px);
      padding: var(--stapel-space-2, 8px) var(--stapel-space-3, 12px);
    }
  `}message(){let e=this.envelope;return e?e.localizable_error?this.i18n.t(e.localizable_error,e.params):e.error||this.i18n.t("admin.attributes.error.generic"):""}render(){return this.envelope?a`<div class="err" role="alert">${this.message()}</div>`:a``}};m([g({attribute:!1})],W.prototype,"envelope",2),m([g({attribute:!1})],W.prototype,"i18n",2);typeof customElements<"u"&&!customElements.get("stapel-error")&&customElements.define("stapel-error",W);var B=class{constructor(t,e={}){this.locale=t;let i=e.en??{},s=e[t]??{};this.catalog={...i,...s}}t(t,e){let i=this.catalog[t]??t;if(e)for(let[s,r]of Object.entries(e))i=i.split(`{${s}}`).join(String(r));return i}has(t){return t in this.catalog}};function Be(n,t){let e=document.createElement("div"),i=document.createElement("h3");i.textContent=t.t("admin.attributes.test.title");let s=document.createElement("div"),r=document.createElement("div");r.style.marginTop="12px",r.style.color="var(--stapel-color-text-muted, #6b7280)",r.textContent=t.t("admin.attributes.test.dto");let o=document.createElement("pre");o.textContent="null";let l=X(n.type)({config:n,i18n:t,onChange:c=>{o.textContent=JSON.stringify(c,null,2)}});return s.appendChild(l),e.append(i,s,r,o),We(e)}function ht(n,t){let e=new B(t.locale??"en",t.messages??{}),i=new x;return i.declaration=t.declaration,i.typeSlug=t.slug,i.i18n=e,i.prefixName=t.prefixName??"",i.translateMode=t.translateMode??"all",i.onConfigChange=t.onChange,n.appendChild(i),t.config&&i.setConfig(t.config),i}function mt(n){return X(n.config.type)(n)}var ft=qe(),gt=Object.assign(ft,{I18n:B,mountConfigEditor:ht,createValueEditor:mt,openTestDialog:Be,ConfigEditor:x});typeof window<"u"&&(window.StapelAttributes=gt);export{x as ConfigEditorElement,B as I18n,mt as createValueEditor,ht as mountConfigEditor,Be as openTestDialog,X as resolveValueEditor};

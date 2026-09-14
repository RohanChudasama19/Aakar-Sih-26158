import {mkdir,copyFile,cp} from 'node:fs/promises';
await mkdir('web/vendor',{recursive:true});
await copyFile('node_modules/three/build/three.module.js','web/vendor/three.module.js');
await copyFile('node_modules/three/build/three.core.js','web/vendor/three.core.js');
await cp('node_modules/three/examples/jsm','web/vendor/addons',{recursive:true});
await copyFile('node_modules/three/LICENSE','web/vendor/THREE-LICENSE');

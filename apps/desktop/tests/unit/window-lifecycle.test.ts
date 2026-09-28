import { expect, it } from "vitest"; import { clampBounds } from "../../electron/main/window-lifecycle";
it("clamps companion DIP bounds into the active display",()=>{ expect(clampBounds({x:5000,y:-20,width:176,height:176},{x:100,y:100,width:1000,height:800})).toEqual({x:924,y:100,width:176,height:176}); });

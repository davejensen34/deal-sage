import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {ResearchTrailView,Trail} from './ResearchTrail';

describe('ResearchTrailView',()=>{it('shows a held boundary without implying ownership',()=>{const trail:Trail={business:{name:'Example Co'},target_profile:null,owner_research_ready:false,readiness_explanation:'Registered Agent does not establish current control.',stages:[{id:1,type:'relationship_validated',sequence:7,status:'insufficient_evidence',confidence:82,detail:'Filed role retained.',supporting_evidence:[],contradictions:[],missing_evidence:['Current controlling-owner evidence'],source:null}]};render(<ResearchTrailView trail={trail}/>);expect(screen.getByText('Not ready for transition-signal research')).toBeInTheDocument();expect(screen.getByText(/does not establish current control/)).toBeInTheDocument();expect(screen.getByText(/Current controlling-owner evidence/)).toBeInTheDocument()})});

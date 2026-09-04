import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {CaseNarratives} from './CaseNarratives';

describe('CaseNarratives',()=>{
  it('keeps model confidence separate from analyst judgment',()=>{
    render(<CaseNarratives cases={[{id:7,origin_strategy:'signal_first',status:'stopped',stop_reason:'frontier_resolved',hypothesis:{direction:'person_to_business',subject:'Jordan Lee',candidate:'Summit Works',status:'proposed'},confidence:{business_identity:90,owner_relationship:72,transition_identity:85,operating_status:60,overall_opportunity:72,method_version:'v1',factors:[]},searches:[],evidence:[],conflicts:[{type:'relationship',rationale:'A later filing names a different owner.',status:'open'}],frontier:[],steps:[],conclusion:null}]}/>);
    expect(screen.getByText('72% opportunity')).toBeInTheDocument();
    expect(screen.getByText(/not a human decision/i)).toBeInTheDocument();
    expect(screen.getByText(/different owner/i)).toBeInTheDocument();
  });
});

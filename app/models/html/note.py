from xml.etree import ElementTree as ET

class NoteHtml(object): 
    @property
    def refs(self):
        html = []
        for ref in self.ref:
            html.append(f'<a href"#" data-bs-toggle="tooltip" data-bs-original-title="{ref.content}">{ref.fullkey}</a>')

        return ','.join(html)

    @property
    def fullkey_html(self):
        fkt = self.fullkeyto
        if "-" in fkt:
            fkt1,fkt2 = fkt.split("-")
            rec,num = fkt2.split(" ")
            fkt = f'{fkt1}-<span class="badge bg-secondary">{rec}</span> {num}'

        if len(self.receivers) > 1:
            return f'<span data-bs-toggle="tooltip" title="{self.receivers}">{fkt}</span>'
        else:
            return f'<span>{fkt}</span>'

    def row_decoration(self,reg,user):
        rg = reg.split('_')

        if rg[0] == 'min':
            if self.sender == user: # The one who wrote the minuta
                if self.state in [0,5]:
                    return '<tr class="fw-bold">'
                elif self.state == 6:
                    return '<tr class="fst-italic">'
            else:
                if not self.is_read(user):
                    return '<tr class="fw-bold">'
                elif self.state == 6:
                    return '<tr class="fst-italic">'
        elif rg[0] in ['cr','cl']:
            if self.rel_flow(reg) == 'in':
                if not self.is_read(user):
                    return '<tr class="fw-bold">'
                elif self.state == 6:
                    return '<tr class="fst-italic">'
            else:
                if self.state in [0,5]:
                    return '<tr class="fw-bold">'
                elif self.state == 6:
                    return '<tr class="text-muted">'



        return "<tr>"

    def state_html(self,reg,user):
        rg = reg.split("_")
        if rg[0] == 'cl': # Es el registro de un centro
            if self.flow == 'out':
                if self.is_read(user):
                    if self.is_read(reg):
                        a = ET.Element('a',attrib={'href':f'?reg={reg}&cldone={self.id}','data-bs-toggle':'tooltip','title':'Mark as undone'})
                        i = ET.Element('i',attrib={'class':'bi bi-envelope-open-fill','style':'color: gray;'})
                    else:
                        a = ET.Element('a',attrib={'href':f'?reg={reg}&cldone={self.id}','data-bs-toggle':'tooltip','title':'Mark as done'})
                        i = ET.Element('i',attrib={'class':'bi bi-envelope-open-fill','style':'color: orange;'})
                else:
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Mark as read'})
                    if self.is_read(reg):
                        i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: gray;'})
                    else:
                        i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: orange;'})
            else: # Note out of cl register
                if self.state == 0: # The cl is working on it
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Send note to cr'})
                    i = ET.Element('i',attrib={'class':'bi bi-send','style':'color: gray;'})
                elif self.state == 1:
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Unsend note to cr'})
                    i = ET.Element('i',attrib={'class':'bi bi-send','style':'color: green;'})
                elif self.state in [2,3,4]:
                    a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Note has been received'})
                    i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: gray;'})
                elif self.state == 5:
                    a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'cr is working on it'})
                    i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: blue;'})
                elif self.state == 6:
                    a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Done'})
                    i = ET.Element('i',attrib={'class':'bi bi-check-all','style':'color: blue;'})
        elif rg[0] == 'des': # For the despacho
            if self.is_read(f"des_{user.alias}"):
                a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as not view'})
                i = ET.Element('i',attrib={'class':'bi bi-envelope-open-fill','style':'color: gray;'})
            else:
                a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as view'})
                i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: orange;'})
        elif rg[0] == 'box':
            a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Archive the note'})
            if rg[1] == 'in':
                i = ET.Element('i',attrib={'class':'bi bi-floppy2','style':'color: orange;'})
            else:
                i = ET.Element('i',attrib={'class':'bi bi-send','style':'color: orange;'})
        elif self.reg in ['cg','asr','r','ctr']:
            if self.rel_flow(reg) == 'in':
                if self.state in [4,5]:
                    if self.is_read(user):
                        if self.is_involve(user):
                            a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as done'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-open-fill','style':'color: orange;'})
                        else:
                            a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Working on it'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-open','style':'color: orange;'})
                    else:
                        a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Mark as read'})
                        if self.is_involve(user):
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: orange;'})
                        else:
                            i = ET.Element('i',attrib={'class':'bi bi-envelope','style':'color: orange;'})
                elif self.state == 6:
                    if self.is_read(user):
                        if self.is_involve(user):
                            a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as undone'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-open-fill','style':'color: gray;'})
                        else:
                            a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Done'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-open','style':'color: gray;'})
                    else:
                        a = ET.Element('a',attrib={'href':f'?reg={reg}&read={self.id}','data-bs-toggle':'tooltip','title':'Mark as read'})
                        if self.is_involve(user):
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: gray;'})
                        else:
                            i = ET.Element('i',attrib={'class':'bi bi-envelope','style':'color: gray;'})
                        
            else: #rel_flow == out
                if self.state in [4,5,6]:
                    if self.sender == user:
                        if self.state == 6:
                            a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as undone'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: gray;'})
                        else:
                            a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as done'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope-fill','style':'color: orange;'})
                    else:
                        if self.state == 6:
                            a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Done'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope','style':'color: gray;'})
                        else:
                            a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Working on it'})
                            i = ET.Element('i',attrib={'class':'bi bi-envelope','style':'color: orange;'})
                else: # I am the sender and I can send or see the status
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Send note'})
                    i = ET.Element('i',attrib={'class':'bi bi-envelope','style':'color: orange;'}) 
        elif self.reg == 'min': # For the minutas
            if self.sender == user:
                if self.state == 0: # Sender is working on it
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Start circulation minuta'})
                    i = ET.Element('i',attrib={'class':'bi bi-hourglass-top','style':'color: green;'})
                elif self.state == 4:
                    a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':f'Circulating ({self.read_by})'})
                    i = ET.Element('i',attrib={'class':'bi bi-hourglass-split','style':'color: gray;'})
                elif self.state == 2:
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Circulation done. Mark as done'})
                    i = ET.Element('i',attrib={'class':'bi bi-hourglass-bottom','style':'color: red;'})
                elif self.state == 6:
                    a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Mark as undone'})
                    i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: blue;'})
            else:
                if self.state <= 5:
                    if not self.is_read(user): # User has already done this note
                        a = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}','data-bs-toggle':'tooltip','title':'Pass to the next one'})
                        i = ET.Element('i',attrib={'class':'bi bi-hourglass-split','style':'color: red;'})
                    else: 
                        a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':f'Circulating ({self.read_by})'})
                        i = ET.Element('i',attrib={'class':'bi bi-hourglass-split','style':'color: gray;'})
                elif self.state == 6:
                    a = ET.Element('span',attrib={'data-bs-toggle':'tooltip','title':'Done'})
                    i = ET.Element('i',attrib={'class':'bi bi-check','style':'color: blue;'})
        
        if self.reg == 'min' and self.sender == user and self.state == 2:
            div = ET.Element('span')
            a2 = ET.Element('a',attrib={'href':f'?reg={reg}&state={self.id}&again=true','data-bs-toggle':'tooltip','title':'Circulate minuta again from beginning'})
            i2 = ET.Element('i',attrib={'class':'bi bi-hourglass-bottom','style':'color: green;'})
            a.append(i)
            a2.append(i2)
            div.append(a)
            div.append(a2)
            rst = div
        else:
            a.append(i)
            rst = a
        return ET.tostring(rst,encoding='unicode',method='html')


                

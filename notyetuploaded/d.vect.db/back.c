#include <stdio.h>
#include <string.h>
#include <X11/Intrinsic.h>
#include <Xm/Xm.h>
#include <Xm/DialogS.h>
#include <Xm/DrawingA.h>
#include <Xm/DrawnB.h>
#include <Xm/Form.h>
#include <Xm/Frame.h>
#include <Xm/Label.h>
#include <Xm/List.h>
#include <Xm/MessageB.h>
#include <Xm/PushB.h>
#include <Xm/RowColumn.h>
#include <Xm/ScrolledW.h>
#include <Xm/ScrollBar.h>
#include <Xm/SelectioB.h>
#include <Xm/Separator.h>
#include <Xm/Text.h>
#include <Xm/ToggleB.h>
#include "Table.h"
#include "TableP.h"
#define INPUT		100
#define OUTPUT	101
#define UNITS		102
#define DISTANCES	103

char *options[] ={"meters","kilometers","feet","miles"};
char *cmd="r.buffer";
char *in_p="input=";
char *out_p="output=";
char *distance_p="distances=";
char *unit_p="units=";
char **values;
Widget shell,buffer_dialog;
Widget Create_Buffer_Dialog(),Create_Input_Cell(),Create_Output_Cell();
Widget Create_Unit_Cell(),Create_Assign_Cell();
void DoBufferDialog(),CallFile(),CallUnit(),CallInputOutput(),UpdateCommand();
void CallOk(),CallCancel(),CallReset(),CallAccept();
XFontStruct *font1=NULL,*font2=NULL;
XmFontList fontlist1=NULL,fontlist2=NULL;
char *namestring="helvb12",*zonestring="helvb14";

main(argc,argv)
   int argc;
   char *argv[];
{
   Widget area,button,dialog;
   Arg al[10];
   int ac;
   
   shell=XtInitialize(argv[0],"",NULL,0,&argc,argv);

   area=XtCreateManagedWidget("area",xmRowColumnWidgetClass,shell,NULL,0);

   ac=0;
   XtSetArg(al[ac],XmNlabelString,
     XmStringCreate("Bring Up Buffer dialog:",XmSTRING_DEFAULT_CHARSET)); ac++;
   button=XtCreateManagedWidget("button",xmPushButtonWidgetClass,area,al,ac);

   dialog=Create_Buffer_Dialog(button);

   XtAddCallback(button,XmNactivateCallback,DoBufferDialog,dialog);
   
   XtRealizeWidget(shell);
   XtMainLoop();
}

void DoBufferDialog(w,dialog,ca)
   Widget w,dialog;
   XtPointer ca;
{
   XtManageChild(dialog);
}

Widget Create_Buffer_Dialog(parent)
   Widget parent;
{
   Widget global_board;
   Widget board_1,io_frame,input_board,output_board;
   Widget board_2,unit_board,assign_board;
   Arg al[10];
   int ac;

   ac=0;
   XtSetArg(al[ac],XmNselectionLabelString,
            XmStringCreate("command line",XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNtextString,
            XmStringCreate("r.buffer input= output= distances= units=",
                           XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNapplyLabelString,
            XmStringCreate("Reset",XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNautoUnmanage,FALSE); ac++;
   buffer_dialog=XmCreatePromptDialog(parent,"buffer_dialog",al,ac);
   XmRemoveTabGroup(buffer_dialog);

   XtAddCallback(buffer_dialog,XmNokCallback,CallOk,NULL);
   XtAddCallback(buffer_dialog,XmNcancelCallback,CallCancel,NULL);

   font1=XLoadQueryFont(XtDisplay(buffer_dialog),namestring);
   fontlist1=XmFontListCreate(font1,XmSTRING_DEFAULT_CHARSET);
   font2=XLoadQueryFont(XtDisplay(buffer_dialog),zonestring);
   fontlist2=XmFontListCreate(font2,XmSTRING_DEFAULT_CHARSET);

   global_board=XmCreateRowColumn(buffer_dialog,"global_board",NULL,0);

   	io_frame=XmCreateFrame(global_board,"io_frame",NULL,0);
   	XtManageChild(io_frame);
   	ac=0;
   	XtSetArg(al[ac],XmNpacking,XmPACK_COLUMN); ac++;
   	board_1=XmCreateRowColumn(io_frame,"board_1",al,ac);
   	XtManageChild(board_1);
   		input_board=Create_Input_Cell(board_1);
   		output_board=Create_Output_Cell(board_1);

   	ac=0;
   	XtSetArg(al[ac],XmNorientation,XmHORIZONTAL); ac++;
   	board_2=XmCreateRowColumn(global_board,"board_2",al,ac);
   	XtManageChild(board_2);
   		unit_board=Create_Unit_Cell(board_2);
   		assign_board=Create_Assign_Cell(board_2);

   XtManageChild(global_board);
   return(buffer_dialog);
}

Widget Create_Assign_Cell(parent)
   Widget parent;
{
   Widget assignRC,labelRC,znLB,disLB,table,optionRC,acceptB,resetB;
   XmString *headings = (XmString *)XtCalloc(60,sizeof(XmString));
   Display *dpy=XtDisplay(shell);
   char name[12];
   Arg al[10];
   int ac,i,scr=DefaultScreen(dpy);

   assignRC=XmCreateRowColumn(parent,"assignRC",NULL,0);
   XtManageChild(assignRC);

	ac=0;
       XtSetArg(al[ac],XmNpacking,XmPACK_NONE); ac++;
       labelRC=XmCreateRowColumn(assignRC,"labelRC",al,ac);
	XtManageChild(labelRC);

		ac=0;
		XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
		XtSetArg(al[ac],XmNlabelString,
		     XmStringCreate("zone",XmSTRING_DEFAULT_CHARSET)); ac++;
		znLB=XmCreateLabel(labelRC,"znLB",al,ac);
		XtManageChild(znLB);

		ac=0;
		XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
		XtSetArg(al[ac],XmNlabelString,
		     XmStringCreate("distances",XmSTRING_DEFAULT_CHARSET)); ac++;
              XtSetArg(al[ac],XmNx,80); ac++;
		disLB=XmCreateLabel(labelRC,"disLB",al,ac);
		XtManageChild(disLB);

   	ac=0;
   	for(i=0;i<60;i++) {
      	   sprintf(name,"%3d",i+1);
      	   headings[i] = XmStringCreateLtoR(name,XmSTRING_DEFAULT_CHARSET);
   	}
   	XtSetArg(al[ac],XmNrowHeadings,headings); ac++;
   	XtSetArg(al[ac],XmNrowHeadingFontColor,BlackPixel(dpy,scr)); ac++;
   	XtSetArg(al[ac],XmNtitleFontColor,BlackPixel(dpy,scr)); ac++;
   	XtSetArg(al[ac],XmNrows,60); ac++;
       XtSetArg(al[ac],XmNmarginWidth,2); ac++;
   	XtSetArg(al[ac],XmNcolumns,1); ac++;
   	XtSetArg(al[ac],XmNrowsDisplayed,4); ac++;
   	XtSetArg(al[ac],XmNheadingFontList,fontlist2); ac++;
   	table=XtCreateManagedWidget("table",xmTableWidgetClass,assignRC,al,ac);
	
   	values=(char **)XtMalloc(60*sizeof(char *));
   	for(i=0;i<60;i++) {
   	   values[i]=XtMalloc(10);
      	   sprintf(values[i],"0");
   	}
   	XmTableSetColumn((XmTableWidget)table,1,values);

	ac=0;
	XtSetArg(al[ac],XmNorientation,XmHORIZONTAL); ac++;
	optionRC=XmCreateForm(assignRC,"optionRC",al,ac);
	XtManageChild(optionRC);

		ac=0;
		XtSetArg(al[ac],XmNlabelString,
		     XmStringCreate("Accept",XmSTRING_DEFAULT_CHARSET)); ac++;
		XtSetArg(al[ac],XmNleftAttachment,XmATTACH_FORM); ac++;
              XtSetArg(al[ac],XmNrightAttachment,XmATTACH_POSITION); ac++;
		XtSetArg(al[ac],XmNrightPosition,49); ac++;
		acceptB=XmCreatePushButton(optionRC,"acceptB",al,ac);
		XmAddTabGroup(acceptB);
		XtManageChild(acceptB);
		XtAddCallback(acceptB,XmNactivateCallback,CallAccept,table);

		ac=0;
		XtSetArg(al[ac],XmNlabelString,
		     XmStringCreate("Reset",XmSTRING_DEFAULT_CHARSET)); ac++;
		XtSetArg(al[ac],XmNleftAttachment,XmATTACH_WIDGET); ac++;
		XtSetArg(al[ac],XmNleftWidget,acceptB); ac++;
		XtSetArg(al[ac],XmNrightAttachment,XmATTACH_FORM); ac++;
		resetB=XmCreatePushButton(optionRC,"resetB",al,ac);
		XmAddTabGroup(resetB);
		XtManageChild(resetB);
		XtAddCallback(resetB,XmNactivateCallback,CallReset,table);
	
   return(assignRC);
}

Widget Create_Unit_Cell(parent)
   Widget parent;
{
   Widget frame,rowcol,browser,unit_label;
   WidgetList buttons;
   Arg al[10];
   int ac,i;

   ac=0;
   XtSetArg(al[ac],XmNspacing,7); ac++;
   rowcol=XtCreateManagedWidget("rowcol",
              xmRowColumnWidgetClass,parent,al,ac);

   ac=0;
   XtSetArg(al[ac],XmNlabelString,
               XmStringCreate("unit",XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
   unit_label=XtCreateManagedWidget("unit_label",
              xmLabelWidgetClass,rowcol,al,ac);

   frame=XtCreateManagedWidget("unitframe",
              xmFrameWidgetClass,rowcol,NULL,0);
  
   buttons=(WidgetList)XtMalloc(4 * sizeof(Widget));
   ac=0;
   XtSetArg(al[ac],XmNspacing,14); ac++;
   browser=XmCreateRadioBox(frame,"browser",al,ac);
   for(i=0;i<4;i++){
      ac=0;
      XtSetArg(al[ac],XmNlabelString,
           XmStringCreate(options[i],XmSTRING_DEFAULT_CHARSET)); ac++;
      XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
      buttons[i]=XtCreateManagedWidget(options[i],
                              xmToggleButtonWidgetClass,browser,al,ac);
      XtAddCallback(buttons[i],XmNarmCallback,CallUnit,i);
      XmAddTabGroup(buttons[i]);
   }
   XtManageChild(browser);
   return(rowcol);
}

Widget Create_Input_Cell(parent)
   Widget parent;
{
   Widget input_board,input_label,input_text,select_B;
   Arg al[10];
   int ac;
   Pixmap map;
   Pixel fore,back;

   input_board=XtCreateManagedWidget("input_board",
                                     xmFormWidgetClass,parent,NULL,0);

   input_label=XtCreateManagedWidget("input_label",
                                     xmLabelWidgetClass,input_board,NULL,0);

   select_B=XtCreateManagedWidget("select_B",
                           xmPushButtonWidgetClass,input_board,NULL,0);
   XmAddTabGroup(select_B);
   XtAddCallback(select_B,XmNactivateCallback,CallFile,"raster file");

   ac=0;
   XtSetArg(al[ac],XmNforeground,&fore); ac++;
   XtSetArg(al[ac],XmNbackground,&back); ac++;
   XtGetValues(select_B,al,ac);
   map=XmGetPixmap(XtScreen(select_B),"raster.xbm",fore,back);
   if(map==XmUNSPECIFIED_PIXMAP)
      exit();

   /* setup a input text */
   input_text=XtCreateManagedWidget("input_text",
                                    xmTextWidgetClass,input_board,NULL,0);
   XtAddCallback(input_text,XmNactivateCallback,CallInputOutput,INPUT);
   XtAddCallback(input_text,XmNlosingFocusCallback,CallInputOutput,INPUT);
   XmAddTabGroup(input_text);

   ac=0;
   XtSetArg(al[ac],XmNlabelString,
                   XmStringCreate("INPUT:",XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
   XtSetArg(al[ac],XmNwidth,100); ac++;
   XtSetArg(al[ac],XmNalignment,XmALIGNMENT_BEGINNING); ac++;
   XtSetArg(al[ac],XmNtopAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNleftAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNbottomAttachment,XmATTACH_FORM); ac++;
   XtSetValues(input_label,al,ac);

   ac=0;
   XtSetArg(al[ac],XmNlabelType,XmPIXMAP); ac++;
   XtSetArg(al[ac],XmNlabelPixmap,map); ac++;
   XtSetArg(al[ac],XmNtopAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNleftAttachment,XmATTACH_WIDGET); ac++;
   XtSetArg(al[ac],XmNleftWidget,input_label); ac++;
   XtSetArg(al[ac],XmNbottomAttachment,XmATTACH_FORM); ac++;
   XtSetValues(select_B,al,ac);

   ac=0;
   XtSetArg(al[ac],XmNtopAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNleftAttachment,XmATTACH_WIDGET); ac++;
   XtSetArg(al[ac],XmNleftWidget,select_B); ac++;
   XtSetArg(al[ac],XmNrightAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNbottomAttachment,XmATTACH_FORM); ac++;
   XtSetValues(input_text,al,ac);

   return(input_board);
}

Widget Create_Output_Cell(parent)
   Widget parent;
{
   Widget output_board,output_label,output_text;
   Arg al[10];
   int ac;

   output_board=XtCreateManagedWidget("output_board",
                              xmFormWidgetClass,parent,NULL,0);

   output_label=XtCreateManagedWidget("output_label",
                              xmLabelWidgetClass,output_board,NULL,0);

   output_text=XtCreateManagedWidget("output_text",
                              xmTextWidgetClass,output_board,NULL,0);
   XtAddCallback(output_text,XmNactivateCallback,CallInputOutput,OUTPUT);
   XtAddCallback(output_text,XmNlosingFocusCallback,CallInputOutput,OUTPUT);
   XmAddTabGroup(output_text);

   ac=0;
   XtSetArg(al[ac],XmNlabelString,
                   XmStringCreate("OUTPUT:",XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetArg(al[ac],XmNfontList,fontlist1); ac++;
   XtSetArg(al[ac],XmNwidth,100); ac++;
   XtSetArg(al[ac],XmNalignment,XmALIGNMENT_BEGINNING); ac++;
   XtSetArg(al[ac],XmNtopAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNleftAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNbottomAttachment,XmATTACH_FORM); ac++;
   XtSetValues(output_label,al,ac);

   ac=0;
   XtSetArg(al[ac],XmNtopAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNleftAttachment,XmATTACH_WIDGET); ac++;
   XtSetArg(al[ac],XmNleftWidget,output_label); ac++;
   XtSetArg(al[ac],XmNrightAttachment,XmATTACH_FORM); ac++;
   XtSetArg(al[ac],XmNbottomAttachment,XmATTACH_FORM); ac++;
   XtSetValues(output_text,al,ac);

   return(output_board);
}

void CallFile(w,str,call_data)
   Widget w;
   char *str;
   XmAnyCallbackStruct *call_data;
{
   Widget files;
   Arg al[10];
   int ac;

   ac=0;
   XtSetArg(al[ac],XmNmessageString,
            XmStringCreate(str,XmSTRING_DEFAULT_CHARSET)); ac++;
   files=XmCreateMessageDialog(w,"Select a Raster Map",al,ac);
   XtUnmanageChild(XmMessageBoxGetChild(files,XmDIALOG_HELP_BUTTON));
   XtManageChild(files);
}

void CallUnit(w,op,call_data)
   Widget w;
   int op;
   caddr_t call_data;
{
   char temp[126];

   switch(op){
     case 0: sprintf(temp,"meters");     break;
     case 1: sprintf(temp,"kilometers"); break;
     case 2: sprintf(temp,"feet");       break;
     case 3: sprintf(temp,"miles");      break;
   }
   UpdateCommand(temp,UNITS);
}

void CallInputOutput(w,client,data)
   Widget w;
   int client;
   caddr_t data;
{
   char temp[256];

   sprintf(temp,"%s",XmTextGetString(w));
   UpdateCommand(temp,client);
}

void UpdateCommand(comd,option)
   char *comd;
   int option;
{
   Arg al[10];
   int ac,size;
   char *cmd_string;

   cmd_string=(char *)malloc(556*sizeof(char));
   size=strlen(comd);
   switch(option) {
      case INPUT:
         free(in_p);
         in_p=(char *)malloc((size+6)*sizeof(char));
         sprintf(in_p,"input=%s",comd);
         break;
      case OUTPUT:
         free(out_p);
         out_p=(char *)malloc((size+7)*sizeof(char));
         sprintf(out_p,"output=%s",comd);
         break;
      case UNITS:
         free(unit_p);
         unit_p=(char *)malloc((size+6)*sizeof(char));
         sprintf(unit_p,"units=%s",comd);
         break;
      case DISTANCES:
         free(distance_p);
         distance_p=(char *)malloc((size+11)*sizeof(char));
         sprintf(distance_p,"distances=%s",comd);
         break;
   }
   sprintf(cmd_string,"%s %s",cmd,in_p);
   sprintf(cmd_string,"%s %s",cmd_string,out_p);
   sprintf(cmd_string,"%s %s",cmd_string,distance_p);
   sprintf(cmd_string,"%s %s",cmd_string,unit_p);
   ac=0;
   XtSetArg(al[ac],XmNtextString,
            XmStringCreate(cmd_string,XmSTRING_DEFAULT_CHARSET)); ac++;
   XtSetValues(buffer_dialog,al,ac);
}

void CallOk(w,client,call_data)
   Widget w;
   caddr_t client,call_data;
{
   printf("%s\n",XmTextGetString(XmSelectionBoxGetChild(w,XmDIALOG_TEXT)));
   XtUnmanageChild(w);
} 

void CallCancel(w,client,call_data)
   Widget w;
   caddr_t client,call_data;
{
   XtUnmanageChild(w);
}

void CallAccept(w,tb,call_data)
   Widget w,tb;
   caddr_t call_data;
{
   int i,flag=0,size=0;
   char *dists,*tok;
   char temp[660],buf[11];

   dists=XmTableGetColumn(tb,1);
   sprintf(temp,"none");
   strtok(dists," ");
   if(strcmp(dists,"0")) {
       flag=1;
       sprintf(temp,"%s",dists);
   }
   for(i=1;i<60;i++) {
      tok=(char *)strtok(NULL," ");
      if(strcmp(tok,"0")) {
          if(flag==1) {
             sprintf(buf,",%s",tok);
             strcat(temp,buf);
          }
          else {
             flag=1;
             sprintf(temp,"%s",tok);
          }
      }
   }
   if(!strcmp(temp,"none"))
       UpdateCommand("",DISTANCES);
   else
       UpdateCommand(temp,DISTANCES);
}

void CallReset(w,tb,call_data)
   Widget w,tb;
   caddr_t call_data;
{
   int i;
   
   for(i=0;i<60;i++)
      sprintf(values[i],"0");
   XmTableSetColumn((XmTableWidget)tb,1,values);
   UpdateCommand("",DISTANCES);
}


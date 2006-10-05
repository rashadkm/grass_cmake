#include "xdr.h"

static FILE *_send, *_recv;

void
db__set_protocol_fds (FILE *send, FILE *recv)
{
    _send = send;
    _recv = recv;
}

int
xdr_begin_send(XDR *xdrs)
{
    xdrstdio_create (xdrs, _send, XDR_ENCODE);

    return 0;
}

int
xdr_begin_recv(XDR *xdrs)
{
    xdrstdio_create (xdrs, _recv, XDR_DECODE);

    return 0;
}

int
xdr_end_send(XDR *xdrs)
{
    fflush(_send);
    xdr_destroy (xdrs);

    return 0;
}

int
xdr_end_recv(XDR *xdrs)
{
    xdr_destroy (xdrs);

    return 0;
}
